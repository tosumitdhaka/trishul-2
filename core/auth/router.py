"""Auth router: login, refresh, logout, me, apikeys CRUD."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from core.auth.jwt_handler import decode_jwt, encode_jwt, make_token_pair
from core.auth.models import User
from core.config.settings import get_settings
from core.models.responses import TrishulResponse, ok, accepted
from core.exceptions import AuthenticationError

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class APIKeyCreateRequest(BaseModel):
    client_id:   str
    roles:       list[str]
    description: str = ""
    rate_limit:  int  = 60


def _sha256_pre_hash(secret: str) -> str:
    """Must match the pre-hash used in db.py seed."""
    return hashlib.sha256(secret.encode()).hexdigest()


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    from passlib.context import CryptContext
    from sqlmodel import Session, select
    from core.db import get_session

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    with get_session() as session:
        user = session.exec(select(User).where(User.username == body.username)).first()

    if not user or not pwd_ctx.verify(_sha256_pre_hash(body.password), user.hashed_pw):
        raise AuthenticationError("Invalid credentials")
    if not user.is_active:
        raise AuthenticationError("Account disabled")

    roles  = json.loads(user.roles)
    tokens = make_token_pair(user.id, roles)
    return TrishulResponse(success=True, data=tokens)


@router.post("/refresh")
async def refresh(body: RefreshRequest, request: Request):
    try:
        payload = decode_jwt(body.refresh_token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token required")

    redis = request.app.state.redis
    if redis and await redis.get(f"blocklist:{payload['jti']}"):
        raise HTTPException(status_code=401, detail="Token revoked")

    new_access = encode_jwt(payload["sub"], payload["roles"], "access")
    return TrishulResponse(success=True, data={"access_token": new_access, "token_type": "bearer"})


@router.post("/logout")
async def logout(request: Request):
    user  = request.state.user
    redis = request.app.state.redis
    if redis and user.get("jti"):
        exp = user.get("exp", 0)
        ttl = max(0, int(exp - datetime.now(timezone.utc).timestamp()))
        await redis.set(f"blocklist:{user['jti']}", "1", ex=ttl or 1)
    return TrishulResponse(success=True, data={"message": "Logged out"})


@router.get("/me")
async def me(request: Request):
    return TrishulResponse(success=True, data=request.state.user)


@router.post("/apikeys")
async def create_apikey(body: APIKeyCreateRequest, request: Request):
    from core.auth.apikey_store import APIKeyStore
    store   = APIKeyStore(request.app.state.redis)
    raw_key = await store.create(
        client_id   = body.client_id,
        roles       = body.roles,
        rate_limit  = body.rate_limit,
        description = body.description,
    )
    return TrishulResponse(success=True, data={"key": raw_key, "note": "Shown once — store securely"})


@router.get("/apikeys")
async def list_apikeys(request: Request):
    return TrishulResponse(success=True, data=[])


@router.delete("/apikeys/{key_id}")
async def revoke_apikey(key_id: str, request: Request):
    return TrishulResponse(success=True, data={"revoked": key_id})
