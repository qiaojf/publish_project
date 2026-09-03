from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.core.security import hash_password
from app.db.base import utc_now
from app.db.models.user import User
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import PageResult
from app.schemas.user import UserCreate, UserRead, UserStatusUpdate, UserUpdate


class UserService:
    @staticmethod
    def list(db: Session, *, keyword: str | None, role: str | None, status: str | None, page: int, page_size: int) -> PageResult[UserRead]:
        items, total = UserRepository.list(db, keyword=keyword, role=role, status=status, page=page, page_size=page_size)
        return PageResult(items=[UserRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)

    @staticmethod
    def get(db: Session, user_id: int) -> UserRead:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFound("用户不存在")
        return UserRead.model_validate(user)

    @staticmethod
    def create(db: Session, payload: UserCreate, operator: User) -> UserRead:
        if UserRepository.get_by_username(db, payload.username, include_deleted=True):
            raise BusinessRuleError("用户名已存在")
        user = UserRepository.create(
            db, username=payload.username, name=payload.name, password_hash=hash_password(payload.password),
            role=payload.role.value, status=payload.status.value,
        )
        OperationLogRepository.create(db, user_id=operator.id, action="create_user", target_type="user", target_id=user.id, message=f"创建用户 {user.name}")
        db.commit()
        db.refresh(user)
        return UserRead.model_validate(user)

    @staticmethod
    def update(db: Session, user_id: int, payload: UserUpdate, operator: User) -> UserRead:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFound("用户不存在")
        duplicate = UserRepository.get_by_username(db, payload.username, include_deleted=True)
        if duplicate and duplicate.id != user_id:
            raise BusinessRuleError("用户名已存在")
        user.username = payload.username
        user.name = payload.name
        user.role = payload.role.value
        user.status = payload.status.value
        if payload.password:
            user.password_hash = hash_password(payload.password)
        user.updated_at = utc_now()
        OperationLogRepository.create(db, user_id=operator.id, action="update_user", target_type="user", target_id=user.id, message=f"更新用户 {user.name}")
        db.commit()
        db.refresh(user)
        return UserRead.model_validate(user)

    @staticmethod
    def update_status(db: Session, user_id: int, payload: UserStatusUpdate, operator: User) -> UserRead:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFound("用户不存在")
        if user.id == operator.id and payload.status.value == "disabled":
            raise BusinessRuleError("不能禁用当前登录账号")
        user.status = payload.status.value
        user.updated_at = utc_now()
        action = "enable_user" if payload.status.value == "active" else "disable_user"
        OperationLogRepository.create(db, user_id=operator.id, action=action, target_type="user", target_id=user.id, message=f"{action} {user.name}")
        db.commit()
        db.refresh(user)
        return UserRead.model_validate(user)

    @staticmethod
    def delete(db: Session, user_id: int, operator: User) -> None:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise ResourceNotFound("用户不存在")
        if user.id == operator.id:
            raise BusinessRuleError("不能删除当前登录账号")
        UserRepository.soft_delete(user)
        OperationLogRepository.create(db, user_id=operator.id, action="delete_user", target_type="user", target_id=user.id, message=f"逻辑删除用户 {user.name}")
        db.commit()
