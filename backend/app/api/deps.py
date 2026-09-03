from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.constants import UserRole, UserStatus
from app.core.exceptions import AuthenticationError, PermissionDenied
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.user_repository import UserRepository


bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("请先登录")
    user_id = decode_access_token(credentials.credentials)
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("登录用户不存在")
    if user.status != UserStatus.ACTIVE.value:
        raise PermissionDenied("账号已被禁用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise PermissionDenied("该功能仅管理员可用")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
