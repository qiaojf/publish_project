from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.operation_log import OperationLog


class OperationLogRepository:
    @staticmethod
    def create(db: Session, **values: object) -> OperationLog:
        log = OperationLog(**values)
        db.add(log)
        db.flush()
        return log

    @staticmethod
    def list(
        db: Session, *, user_id: int | None, action: str | None, date_from: datetime | None,
        date_to: datetime | None, page: int, page_size: int,
    ) -> tuple[list[OperationLog], int]:
        filters: list[object] = []
        if user_id:
            filters.append(OperationLog.user_id == user_id)
        if action:
            filters.append(OperationLog.action == action)
        if date_from:
            filters.append(OperationLog.created_at >= date_from)
        if date_to:
            filters.append(OperationLog.created_at <= date_to)
        total = db.scalar(select(func.count()).select_from(OperationLog).where(*filters)) or 0
        statement = select(OperationLog).options(selectinload(OperationLog.user)).where(*filters).order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        return list(db.scalars(statement)), total
