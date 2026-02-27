from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Session, select

from core.auth.apikey_store import (
    add_to_blocklist,
    generate_raw_key,
    store_api_key,
)
from core.auth.jwt_handler import (
    decode_token,
    encode_access_token,
    encode_refresh_token,
)
from core.auth.models import APIKey, User
from core.auth.middleware import require_role
from core.dependencies import current_user
from core.exceptions import AuthenticationError
from core.models.responses import TrishulResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- Request / Response schemas ----------

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenPair(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"

class APIKeyCreate(BaseModel):
    client_id:   str
    roles:       list[str]
    description: str = ""
    rate_limit:  int = 60

class APIKeyResponse(BaseModel):
    id:          str
    client_id:   str
    key:         str   # raw key — shown ONCE
    roles:       list[str]
    description: str


# ---------- Endpoints ----------

@router.post("/login", response_model=TrishulResponse[TokenPair])
async def login(body: LoginRequest, request: Request):
    db: Session = request.app.state.db
    stmt = select(User).where(User.username == body.username, User.is_active == True)  # noqa: E712
    user = db.exec(stmt).first()
    if not user or not _pwd.verify(body.password, user.hashed_pw):
        raise AuthenticationError("Invalid username or password")
    roles = json.loads(user.roles)
    return TrishulResponse.ok(TokenPair(
        access_token=encode_access_token(user.id, user.username, roles),
        refresh_token=encode_refresh_token(user.id),
    ))


@router.post("/refresh", response_model=TrishulResponse[dict])
async def refresh(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise AuthenticationError("Refresh token required")
    payload = decode_token(auth[7:])
    if payload.get("type") != "refresh":
        raise AuthenticationError("Not a refresh token")
    redis: aioredis.Redis = request.app.state.redis
    if await redis.exists(f"blocklist:{payload['jti']}"):
        raise AuthenticationError("Token revoked")
    # Fetch fresh roles from DB
    db: Session = request.app.state.db
    user = db.exec(select(User).where(User.id == payload["sub"])).first()
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    roles = json.loads(user.roles)
    return TrishulResponse.ok({
        "access_token": encode_access_token(user.id, user.username, roles),
        "token_type": "bearer",
    })


@router.post("/logout", response_model=TrishulResponse[dict])
async def logout(request: Request, user: dict = Depends(current_user)):
    if user.get("auth_type") != "jwt":
        return TrishulResponse.ok({"message": "API key sessions do not need explicit logout"})
    jti = user.get("jti", "")
    exp = user.get("exp", 0)
    ttl = max(1, int(exp - datetime.now(timezone.utc).timestamp()))
    redis: aioredis.Redis = request.app.state.redis
    await add_to_blocklist(redis, jti, ttl)
    return TrishulResponse.ok({"message": "Logged out successfully"})


@router.get("/me", response_model=TrishulResponse[dict])
async def me(user: dict = Depends(current_user)):
    return TrishulResponse.ok({k: v for k, v in user.items() if k != "exp"})


@router.post("/apikeys", response_model=TrishulResponse[APIKeyResponse],
             dependencies=[require_role("admin")])
async def create_api_key(body: APIKeyCreate, request: Request):
    raw_key = generate_raw_key()
    redis: aioredis.Redis = request.app.state.redis
    await store_api_key(
        redis, raw_key, body.client_id, body.roles,
        body.rate_limit, body.description,
    )
    # Persist metadata to SQLite (hash only, never raw key)
    db: Session = request.app.state.db
    import hashlib
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key_row = APIKey(
        id=str(uuid.uuid4()),
        client_id=body.client_id,
        key_hash=key_hash,
        roles=json.dumps(body.roles),
        rate_limit=body.rate_limit,
        description=body.description,
    )
    db.add(api_key_row)
    db.commit()
    return TrishulResponse.ok(APIKeyResponse(
        id=api_key_row.id,
        client_id=body.client_id,
        key=raw_key,  # shown once
        roles=body.roles,
        description=body.description,
    ))


@router.get("/apikeys", response_model=TrishulResponse[list],
            dependencies=[require_role("admin")])
async def list_api_keys(request: Request):
    db: Session = request.app.state.db
    keys = db.exec(select(APIKey).where(APIKey.is_active == True)).all()  # noqa: E712
    return TrishulResponse.ok([
        {"id": k.id, "client_id": k.client_id, "roles": json.loads(k.roles),
         "description": k.description, "created_at": str(k.created_at)}
        for k in keys
    ])


@router.delete("/apikeys/{key_id}", response_model=TrishulResponse[dict],
               dependencies=[require_role("admin")])
async def revoke_api_key_endpoint(key_id: str, request: Request):
    db: Session = request.app.state.db
    api_key = db.exec(select(APIKey).where(APIKey.id == key_id)).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    db.add(api_key)
    db.commit()
    return TrishulResponse.ok({"message": "API key revoked"})
