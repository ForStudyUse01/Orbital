from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status

from .config import settings


@dataclass(frozen=True)
class Principal:
    user_id: str
    is_admin: bool = False


def _decode_clerk_token(token: str) -> str:
    if not settings.clerk_issuer:
        raise HTTPException(status_code=503, detail="Authentication provider is not configured")
    jwks_url = f"{settings.clerk_issuer.rstrip('/')}/.well-known/jwks.json"
    signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=settings.clerk_audience,
        issuer=settings.clerk_issuer,
        options={"verify_aud": bool(settings.clerk_audience)},
    )
    subject = claims.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token has no subject")
    return str(subject)


async def require_user(authorization: Annotated[str | None, Header()] = None) -> Principal:
    if authorization and authorization.startswith("Bearer "):
        try:
            user_id = _decode_clerk_token(authorization[7:])
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid authentication token") from exc
        return Principal(user_id, user_id in settings.admin_user_ids)
    if settings.app_env != "production" and settings.dev_auth_user_id:
        user_id = settings.dev_auth_user_id
        return Principal(user_id, user_id in settings.admin_user_ids)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(principal: Annotated[Principal, Depends(require_user)]) -> Principal:
    if not principal.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return principal
