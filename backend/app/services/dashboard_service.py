from sqlalchemy.orm import Session

from app.db.models.content import Content
from app.db.models.user import User
from app.repositories.content_repository import ContentRepository
from app.schemas.dashboard import DashboardRead
from app.services.serializers import content_to_read


class DashboardService:
    @staticmethod
    def get(db: Session, current_user: User) -> DashboardRead:
        scope = [] if current_user.role == "admin" else [Content.created_by == current_user.id]
        recent = ContentRepository.recent(db, *scope, limit=5)
        recent_published = ContentRepository.recent(db, *scope, Content.publish_status == "published", published=True, limit=5)
        common = dict(
            pending_review=ContentRepository.count(db, *scope, Content.review_status == "pending"),
            published=ContentRepository.count(db, *scope, Content.publish_status == "published"),
            recent_submissions=[content_to_read(item) for item in recent],
            recent_publishes=[content_to_read(item) for item in recent_published],
        )
        if current_user.role == "admin":
            return DashboardRead(
                content_total=ContentRepository.count(db),
                publish_failed=ContentRepository.count(db, Content.publish_status == "failed"),
                **common,
            )
        return DashboardRead(
            my_content_total=ContentRepository.count(db, *scope),
            rejected=ContentRepository.count(db, *scope, Content.review_status == "rejected"),
            recent_contents=[content_to_read(item) for item in recent],
            **common,
        )
