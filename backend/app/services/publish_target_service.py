from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.db.base import utc_now
from app.db.models.publish_target import PublishTarget
from app.db.models.user import User
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.publish_target_repository import PublishTargetRepository
from app.schemas.publish_target import (
    PublishTargetAdminRead,
    PublishTargetConnectionRead,
    PublishTargetEmployeeRead,
    PublishTargetPayload,
    PublishTargetStatusUpdate,
    SECRET_FIELD_MARKERS,
)
from app.target_publishers.factory import TargetPublisherFactory


class PublishTargetService:
    @staticmethod
    def _sanitize_config(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: PublishTargetService._sanitize_config(nested)
                for key, nested in value.items()
                if not any(marker in key.lower().replace("-", "_") for marker in SECRET_FIELD_MARKERS)
            }
        if isinstance(value, list):
            return [PublishTargetService._sanitize_config(item) for item in value]
        return value

    @classmethod
    def _admin_read(cls, target: PublishTarget) -> PublishTargetAdminRead:
        result = PublishTargetAdminRead.model_validate(target)
        return result.model_copy(update={"config": cls._sanitize_config(result.config)})

    @staticmethod
    def list(db: Session, current_user: User) -> list[PublishTargetAdminRead | PublishTargetEmployeeRead]:
        targets = PublishTargetRepository.list(db, enabled_only=current_user.role != "admin")
        if current_user.role == "admin":
            return [PublishTargetService._admin_read(item) for item in targets]
        return [PublishTargetEmployeeRead.model_validate(item) for item in targets]

    @staticmethod
    def get_admin(db: Session, target_id: int) -> PublishTargetAdminRead:
        target = PublishTargetRepository.get_by_id(db, target_id)
        if not target:
            raise ResourceNotFound("发布目标不存在")
        return PublishTargetService._admin_read(target)

    @staticmethod
    def create(db: Session, payload: PublishTargetPayload, operator: User) -> PublishTargetAdminRead:
        target = PublishTargetRepository.create(
            db, name=payload.name, content_types=[item.value for item in payload.content_types],
            target_type=payload.target_type.value, config=payload.config, credential_ref=payload.credential_ref,
            publish_root=payload.publish_root, base_url=payload.base_url, enabled=payload.enabled,
            created_by=operator.id,
        )
        OperationLogRepository.create(db, user_id=operator.id, action="create_publish_target", target_type="publish_target", target_id=target.id, message=f"创建发布目标 {target.name}")
        db.commit()
        db.refresh(target)
        return PublishTargetService._admin_read(target)

    @staticmethod
    def update(db: Session, target_id: int, payload: PublishTargetPayload, operator: User) -> PublishTargetAdminRead:
        target = PublishTargetRepository.get_by_id(db, target_id)
        if not target:
            raise ResourceNotFound("发布目标不存在")
        target.name = payload.name
        target.content_types = [item.value for item in payload.content_types]
        target.target_type = payload.target_type.value
        target.config = payload.config
        target.credential_ref = payload.credential_ref
        target.publish_root = payload.publish_root
        target.base_url = payload.base_url
        target.enabled = payload.enabled
        target.updated_at = utc_now()
        OperationLogRepository.create(db, user_id=operator.id, action="update_publish_target", target_type="publish_target", target_id=target.id, message=f"更新发布目标 {target.name}")
        db.commit()
        db.refresh(target)
        return PublishTargetService._admin_read(target)

    @staticmethod
    def update_status(db: Session, target_id: int, payload: PublishTargetStatusUpdate, operator: User) -> PublishTargetAdminRead:
        target = PublishTargetRepository.get_by_id(db, target_id)
        if not target:
            raise ResourceNotFound("发布目标不存在")
        target.enabled = payload.enabled
        target.updated_at = utc_now()
        action = "enable_publish_target" if payload.enabled else "disable_publish_target"
        OperationLogRepository.create(db, user_id=operator.id, action=action, target_type="publish_target", target_id=target.id, message=f"{action} {target.name}")
        db.commit()
        db.refresh(target)
        return PublishTargetService._admin_read(target)

    @staticmethod
    def test_connection(
        db: Session, target_id: int, operator: User,
    ) -> PublishTargetConnectionRead:
        target = PublishTargetRepository.get_by_id(db, target_id)
        if not target:
            raise ResourceNotFound("发布目标不存在")
        connected = TargetPublisherFactory.create(target.target_type).test_connection(target)
        OperationLogRepository.create(
            db, user_id=operator.id, action="test_publish_target", target_type="publish_target",
            target_id=target.id, message=f"测试发布目标连接 {target.name}",
        )
        db.commit()
        return PublishTargetConnectionRead(connected=connected)

    @staticmethod
    def delete(db: Session, target_id: int, operator: User) -> None:
        target = PublishTargetRepository.get_by_id(db, target_id)
        if not target:
            raise ResourceNotFound("发布目标不存在")
        if PublishTargetRepository.is_in_use(db, target_id):
            raise BusinessRuleError("该发布目标已被内容使用，请改为禁用")
        OperationLogRepository.create(db, user_id=operator.id, action="delete_publish_target", target_type="publish_target", target_id=target.id, message=f"删除发布目标 {target.name}")
        db.delete(target)
        db.commit()

    @staticmethod
    def validate_for_content(target: PublishTarget | None, content_type: str) -> None:
        if not target:
            raise BusinessRuleError("请选择有效的发布目标", 422)
        if not target.enabled:
            raise BusinessRuleError("发布目标已禁用")
        if content_type not in target.content_types:
            raise BusinessRuleError("内容类型与发布目标不匹配", 422)
