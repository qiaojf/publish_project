from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.content import Content
from app.db.models.publish_record import PublishRecord
from app.db.models.publish_target import PublishTarget


class PublishTargetRepository:
    @staticmethod
    def get_by_id(db: Session, target_id: int) -> PublishTarget | None:
        return db.get(PublishTarget, target_id)

    @staticmethod
    def list(db: Session, *, enabled_only: bool = False) -> list[PublishTarget]:
        statement = select(PublishTarget)
        if enabled_only:
            statement = statement.where(PublishTarget.enabled.is_(True))
        return list(db.scalars(statement.order_by(PublishTarget.created_at.desc())))

    @staticmethod
    def create(db: Session, **values: object) -> PublishTarget:
        target = PublishTarget(**values)
        db.add(target)
        db.flush()
        return target

    @staticmethod
    def is_in_use(db: Session, target_id: int) -> bool:
        content_count = db.scalar(
            select(func.count()).select_from(Content).where(Content.publish_target_id == target_id)
        ) or 0
        publish_count = db.scalar(
            select(func.count()).select_from(PublishRecord).where(PublishRecord.publish_target_id == target_id)
        ) or 0
        return content_count > 0 or publish_count > 0
