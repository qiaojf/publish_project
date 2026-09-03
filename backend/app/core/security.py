from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expires_at, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        if subject is None:
            raise AuthenticationError("Token 缺少用户标识")
        return int(subject)
    except (InvalidTokenError, TypeError, ValueError) as exc:
        raise AuthenticationError("登录状态无效或已过期") from exc
