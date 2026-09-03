from sqlalchemy.orm import Session

from app.core.constants import UserStatus
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, verify_password
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResult
from app.schemas.user import CurrentUserRead


class AuthService:
    @staticmethod
    def login(db: Session, username: str, password: str, ip_address: str | None = None) -> LoginResult:
        user = UserRepository.get_by_username(db, username.strip())
        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("用户名或密码错误")
        if user.status != UserStatus.ACTIVE.value:
            raise AuthenticationError("账号已被禁用")
        OperationLogRepository.create(
            db, user_id=user.id, action="login", target_type="user", target_id=user.id,
            message="登录内容发布平台", ip_address=ip_address,
        )
        db.commit()
        return LoginResult(token=create_access_token(user.id), user=CurrentUserRead.model_validate(user))
