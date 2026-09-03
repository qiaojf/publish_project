from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.base import utc_now
from app.db.models.content import Content
from app.db.models.publish_record import PublishRecord
from app.db.models.review_record import ReviewRecord


CONTENT_LOADERS = (
    selectinload(Content.creator),
    selectinload(Content.publish_target),
    selectinload(Content.review_records).selectinload(ReviewRecord.operator),
    selectinload(Content.publish_records).selectinload(PublishRecord.publish_target),
)


class ContentRepository:
    @staticmethod
    def get_by_id(db: Session, content_id: int) -> Content | None:
        return db.scalar(select(Content).options(*CONTENT_LOADERS).where(Content.id == content_id, Content.deleted_at.is_(None)))

    @staticmethod
    def get_for_update(db: Session, content_id: int) -> Content | None:
        return db.scalar(select(Content).where(Content.id == content_id, Content.deleted_at.is_(None)).with_for_update())

    @staticmethod
    def list(
        db: Session, *, user_id: int | None, keyword: str | None, content_type: str | None,
        category: str | None, review_status: str | None, publish_status: str | None,
        created_by: int | None, page: int, page_size: int,
    ) -> tuple[list[Content], int]:
        filters = [Content.deleted_at.is_(None)]
        if user_id is not None:
            filters.append(Content.created_by == user_id)
        elif created_by is not None:
            filters.append(Content.created_by == created_by)
        if keyword:
            term = f"%{keyword}%"
            filters.append(or_(Content.title.ilike(term), Content.description.ilike(term)))
        if content_type:
            filters.append(Content.content_type == content_type)
        if category:
            filters.append(Content.category == category)
        if review_status:
            filters.append(Content.review_status == review_status)
        if publish_status:
            filters.append(Content.publish_status == publish_status)
        total = db.scalar(select(func.count()).select_from(Content).where(*filters)) or 0
        statement = select(Content).options(*CONTENT_LOADERS).where(*filters).order_by(Content.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(db.scalars(statement)), total

    @staticmethod
    def list_reviews(
        db: Session, *, status: str, keyword: str | None, content_type: str | None, category: str | None,
        submitted_by: str | None, date_from: datetime | None, date_to: datetime | None, page: int, page_size: int,
    ) -> tuple[list[Content], int]:
        from app.db.models.user import User

        filters = [Content.deleted_at.is_(None), Content.review_status == status]
        if keyword:
            filters.append(Content.title.ilike(f"%{keyword}%"))
        if content_type:
            filters.append(Content.content_type == content_type)
        if category:
            filters.append(Content.category == category)
        if date_from:
            filters.append(Content.updated_at >= date_from)
        if date_to:
            filters.append(Content.updated_at <= date_to)
        base = select(Content).join(Content.creator)
        count_base = select(func.count()).select_from(Content).join(Content.creator)
        if submitted_by:
            filters.append(or_(User.name.ilike(f"%{submitted_by}%"), User.username.ilike(f"%{submitted_by}%")))
        total = db.scalar(count_base.where(*filters)) or 0
        statement = base.options(*CONTENT_LOADERS).where(*filters).order_by(Content.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(db.scalars(statement)), total

    @staticmethod
    def create(db: Session, **values: object) -> Content:
        content = Content(**values)
        db.add(content)
        db.flush()
        return content

    @staticmethod
    def soft_delete(content: Content) -> None:
        content.deleted_at = utc_now()
        content.updated_at = utc_now()

    @staticmethod
    def search_published(
        db: Session, *, keyword: str | None, content_type: str | None, category: str | None,
        date_from: datetime | None, date_to: datetime | None, page: int, page_size: int,
    ) -> tuple[list[Content], int]:
        filters = [Content.deleted_at.is_(None), Content.publish_status == "published"]
        if keyword:
            term = f"%{keyword}%"
            filters.append(or_(Content.title.ilike(term), Content.description.ilike(term)))
        if content_type:
            filters.append(Content.content_type == content_type)
        if category:
            filters.append(Content.category == category)
        if date_from:
            filters.append(Content.published_at >= date_from)
        if date_to:
            filters.append(Content.published_at <= date_to)
        total = db.scalar(select(func.count()).select_from(Content).where(*filters)) or 0
        statement = select(Content).options(*CONTENT_LOADERS).where(*filters).order_by(Content.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(db.scalars(statement)), total

    @staticmethod
    def count(db: Session, *filters: object) -> int:
        return db.scalar(select(func.count()).select_from(Content).where(Content.deleted_at.is_(None), *filters)) or 0

    @staticmethod
    def recent(db: Session, *filters: object, published: bool = False, limit: int = 5) -> list[Content]:
        order = Content.published_at.desc() if published else Content.updated_at.desc()
        statement = select(Content).options(*CONTENT_LOADERS).where(Content.deleted_at.is_(None), *filters).order_by(order).limit(limit)
        return list(db.scalars(statement))
