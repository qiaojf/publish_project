from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFound
from app.db.models.category import Category
from app.db.models.content import Content
from app.db.models.department import Department
from app.db.models.operation_log import OperationLog
from app.db.models.publish_target import PublishTarget
from app.db.models.user import User
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.publish_record_repository import PublishRecordRepository
from app.schemas.common import PageResult
from app.schemas.publish_record import OperationLogRead, PublishRecordRead
from app.services.serializers import operation_log_to_read, publish_record_to_read


class LogService:
    @staticmethod
    def _operation_targets(db: Session, items: list[OperationLog]) -> dict[tuple[str, int], str]:
        labels: dict[tuple[str, int], str] = {}
        model_fields = {
            "category": (Category, Category.name),
            "user": (User, User.username),
            "content": (Content, Content.title),
            "department": (Department, Department.name),
            "publish_target": (PublishTarget, PublishTarget.name),
        }
        for target_type, (model, field) in model_fields.items():
            ids = {item.target_id for item in items if item.target_type == target_type and item.target_id is not None}
            if not ids:
                continue
            for target_id, label in db.execute(select(model.id, field).where(model.id.in_(ids))):
                labels[(target_type, target_id)] = label
        return labels

    @staticmethod
    def operation_logs(db: Session, *, user_id: int | None, action: str | None, date_from: datetime | None, date_to: datetime | None, page: int, page_size: int) -> PageResult[OperationLogRead]:
        items, total = OperationLogRepository.list(db, user_id=user_id, action=action, date_from=date_from, date_to=date_to, page=page, page_size=page_size)
        targets = LogService._operation_targets(db, items)
        return PageResult(
            items=[
                operation_log_to_read(
                    item,
                    target=targets.get((item.target_type, item.target_id))
                    if item.target_type and item.target_id is not None else None,
                )
                for item in items
            ],
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def publish_records(db: Session, *, content_id: int | None, keyword: str | None, status: str | None, content_type: str | None, date_from: datetime | None, date_to: datetime | None, page: int, page_size: int) -> PageResult[PublishRecordRead]:
        items, total = PublishRecordRepository.list(db, content_id=content_id, keyword=keyword, status=status, content_type=content_type, date_from=date_from, date_to=date_to, page=page, page_size=page_size)
        return PageResult(items=[publish_record_to_read(item) for item in items], total=total, page=page, page_size=page_size)

    @staticmethod
    def publish_record(db: Session, record_id: int) -> PublishRecordRead:
        record = PublishRecordRepository.get_by_id(db, record_id)
        if not record:
            raise ResourceNotFound("发布记录不存在")
        return publish_record_to_read(record)
