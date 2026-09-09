from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.content_repository import ContentRepository
from app.schemas.common import PageResult
from app.schemas.content import ContentRead
from app.services.serializers import content_to_read


class SearchService:
    @staticmethod
    def search(
        db: Session, current_user: User, *, keyword: str | None, content_type: str | None, category: str | None,
        publish_target_id: int | None, department: str | None,
        date_from: datetime | None, date_to: datetime | None, page: int, page_size: int,
    ) -> PageResult[ContentRead]:
        items, total = ContentRepository.search_published(
            db, keyword=keyword, content_type=content_type, category=category,
            publish_target_id=publish_target_id, department=department,
            date_from=date_from, date_to=date_to,
            viewer_id=None if current_user.role == "admin" else current_user.id,
            viewer_department=current_user.department, page=page, page_size=page_size,
        )
        return PageResult(items=[content_to_read(item) for item in items], total=total, page=page, page_size=page_size)
