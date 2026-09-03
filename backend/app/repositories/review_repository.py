from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.review_record import ReviewRecord


class ReviewRepository:
    @staticmethod
    def create_record(db: Session, **values: object) -> ReviewRecord:
        record = ReviewRecord(**values)
        db.add(record)
        db.flush()
        return record

    @staticmethod
    def list_by_content(db: Session, content_id: int) -> list[ReviewRecord]:
        statement = select(ReviewRecord).options(selectinload(ReviewRecord.operator)).where(ReviewRecord.content_id == content_id).order_by(ReviewRecord.created_at.desc())
        return list(db.scalars(statement))
