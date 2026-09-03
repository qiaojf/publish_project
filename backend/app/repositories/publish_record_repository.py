from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.content import Content
from app.db.models.publish_record import PublishRecord


PUBLISH_LOADERS = (
    selectinload(PublishRecord.content),
    selectinload(PublishRecord.publish_target),
    selectinload(PublishRecord.triggered_by_user),
)


class PublishRecordRepository:
    @staticmethod
    def create(db: Session, **values: object) -> PublishRecord:
        record = PublishRecord(**values)
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def get_by_id(db: Session, record_id: int) -> PublishRecord | None:
        return db.scalar(select(PublishRecord).options(*PUBLISH_LOADERS).where(PublishRecord.id == record_id))

    @staticmethod
    def list(
        db: Session, *, content_id: int | None, keyword: str | None, status: str | None, content_type: str | None,
        date_from: datetime | None, date_to: datetime | None, page: int, page_size: int,
    ) -> tuple[list[PublishRecord], int]:
        filters: list[object] = []
        if content_id:
            filters.append(PublishRecord.content_id == content_id)
        if keyword:
            filters.append(Content.title.ilike(f"%{keyword.strip()}%"))
        if status:
            filters.append(PublishRecord.status == status)
        if date_from:
            filters.append(PublishRecord.created_at >= date_from)
        if date_to:
            filters.append(PublishRecord.created_at <= date_to)
        base = select(PublishRecord).join(PublishRecord.content)
        count_base = select(func.count()).select_from(PublishRecord).join(PublishRecord.content)
        if content_type:
            filters.append(Content.content_type == content_type)
        total = db.scalar(count_base.where(*filters)) or 0
        statement = base.options(*PUBLISH_LOADERS).where(*filters).order_by(PublishRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(db.scalars(statement)), total

    @staticmethod
    def list_by_content(db: Session, content_id: int) -> list[PublishRecord]:
        return list(db.scalars(select(PublishRecord).options(*PUBLISH_LOADERS).where(PublishRecord.content_id == content_id).order_by(PublishRecord.created_at.desc())))
