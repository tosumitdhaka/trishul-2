"""Auth router — /api/v1/auth/*

Endpoints:
  POST /login           → username + password → TokenPair
  POST /refresh         → refresh JWT → new access token
  POST /logout          → access JWT → add jti to Redis blocklist
  GET  /me              → current user info
  GET  /apikeys         → list API keys (admin)
  POST /apikeys         → create API key (admin)
  DELETE /apikeys/{id}  → revoke API key (admin)
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext
from sqlmodel import Session, select

from core.auth.apikey_store import (
    cache_key_in_redis,
    generate_raw_key,
    hash_key,
    revoke_key_in_redis,
)
from core.auth.jwt_handler import (
    AuthenticationError,
    decode_jwt,
    encode_jwt,
    token_remaining_seconds,
)
from core.auth.middleware import require_role
from core.auth.models import APIKey, AuditLog, User
from core.dependencies import CurrentUser
from core.models.responses import TrishulResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db(request: Request):
    return request.app.state.db


# ─── Login ────────────────────────────────────────────────────────────────────────

class LoginRequest(TrishulResponse):
    pass  # placeholder import works; actual input defined below


from pydantic import BaseModel


class _LoginIn(BaseModel):
    username: str
    password: str


class _TokenPair(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


@router.post("/login", response_model=TrishulResponse)
def login(body: _LoginIn, request: Request, db: Session = Depends(get_db)):
    user = db.exec(select(User).where(User.username == body.username)).first()
    if not user or not pwd_ctx.verify(body.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    roles = json.loads(user.roles)
    return TrishulResponse.ok(
        data=_TokenPair(
            access_token=encode_jwt(user.id, roles, "access"),
            refresh_token=encode_jwt(user.id, roles, "refresh"),
        ).model_dump()
    )


# ─── Refresh ──────────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TrishulResponse)
async def refresh(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Refresh token required")
    token = auth_header[7:]
    try:
        payload = decode_jwt(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    redis = request.app.state.redis
    if await redis.exists(f"blocklist:{payload['jti']}"):
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    new_access = encode_jwt(payload["sub"], payload.get("roles", []), "access")
    return TrishulResponse.ok(data={"access_token": new_access, "token_type": "bearer"})


# ─── Logout ──────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=TrishulResponse)
async def logout(request: Request, user: CurrentUser):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return TrishulResponse.ok(data={"logged_out": True})

    token = auth_header[7:]
    try:
        payload = decode_jwt(token)
    except AuthenticationError:
        return TrishulResponse.ok(data={"logged_out": True})  # already invalid

    jti = payload.get("jti", "")
    ttl = token_remaining_seconds(payload)
    if jti and ttl > 0:
        redis = request.app.state.redis
        await redis.setex(f"blocklist:{jti}", ttl, "1")

    return TrishulResponse.ok(data={"logged_out": True})


# ─── Me ────────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=TrishulResponse)
def me(user: CurrentUser):
    return TrishulResponse.ok(data=user)


# ─── API Keys ─────────────────────────────────────────────────────────────────────

class _CreateKeyIn(BaseModel):
    client_id:   str
    roles:       list[str] = ["viewer"]
    description: str       = ""
    rate_limit:  int       = 600


@router.get("/apikeys", response_model=TrishulResponse, dependencies=[require_role("admin")])
def list_apikeys(db: Session = Depends(get_db)):
    keys = db.exec(select(APIKey).where(APIKey.is_active == True)).all()  # noqa: E712
    return TrishulResponse.ok(data=[
        {"id": k.id, "client_id": k.client_id, "roles": json.loads(k.roles),
         "rate_limit": k.rate_limit, "description": k.description,
         "created_at": k.created_at.isoformat()}
        for k in keys
    ])


@router.post("/apikeys", response_model=TrishulResponse, dependencies=[require_role("admin")])
async def create_apikey(
    body: _CreateKeyIn,
    request: Request,
    db: Session = Depends(get_db),
):
    raw_key  = generate_raw_key()
    key_hash = hash_key(raw_key)

    api_key = APIKey(
        client_id=body.client_id,
        key_hash=key_hash,
        roles=json.dumps(body.roles),
        rate_limit=body.rate_limit,
        description=body.description,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Cache in Redis for fast auth lookups
    redis = request.app.state.redis
    await cache_key_in_redis(redis, api_key)

    return TrishulResponse.ok(data={
        "id":      api_key.id,
        "key":     raw_key,   # Shown ONCE. Not stored.
        "message": "Store this key securely. It will not be shown again.",
    })


@router.delete("/apikeys/{key_id}", response_model=TrishulResponse, dependencies=[require_role("admin")])
async def revoke_apikey(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    api_key = db.get(APIKey, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.is_active = False
    db.add(api_key)
    db.commit()

    redis = request.app.state.redis
    await revoke_key_in_redis(redis, api_key.key_hash)

    return TrishulResponse.ok(data={"revoked": True, "id": key_id})
