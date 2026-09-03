from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import PublishStatus, ReviewAction, ReviewStatus
from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.db.base import utc_now
from app.db.models.user import User
from app.repositories.content_repository import ContentRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.common import PageResult
from app.schemas.content import ContentRead
from app.schemas.publish_target import PublishTargetAdminRead
from app.schemas.review import ReviewDetailRead
from app.services.publish_service import PublishService
from app.services.serializers import content_to_read, review_to_read


class ReviewService:
    @staticmethod
    def list(
        db: Session, *, status: str, keyword: str | None, content_type: str | None,
        category: str | None, submitted_by: str | None, date_from: datetime | None,
        date_to: datetime | None, page: int, page_size: int,
    ) -> PageResult[ContentRead]:
        items, total = ContentRepository.list_reviews(
            db, status=status, keyword=keyword, content_type=content_type, category=category,
            submitted_by=submitted_by, date_from=date_from, date_to=date_to, page=page, page_size=page_size,
        )
        return PageResult(items=[content_to_read(item) for item in items], total=total, page=page, page_size=page_size)

    @staticmethod
    def detail(db: Session, content_id: int) -> ReviewDetailRead:
        content = ContentRepository.get_by_id(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        history = ReviewRepository.list_by_content(db, content_id)
        target = PublishTargetAdminRead.model_validate(content.publish_target) if content.publish_target else None
        return ReviewDetailRead(content=content_to_read(content, include_body=True), publish_target=target, history=[review_to_read(item) for item in history])

    @staticmethod
    def reject(db: Session, content_id: int, comment: str, operator: User) -> ContentRead:
        content = ContentRepository.get_for_update(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        if content.review_status != ReviewStatus.PENDING.value:
            raise BusinessRuleError("仅待审核内容可以驳回")
        content.review_status = ReviewStatus.REJECTED.value
        content.publish_status = PublishStatus.UNPUBLISHED.value
        content.reject_reason = comment.strip()
        content.updated_at = utc_now()
        ReviewRepository.create_record(db, content_id=content.id, action=ReviewAction.REJECT.value, from_status=ReviewStatus.PENDING.value, to_status=ReviewStatus.REJECTED.value, comment=comment.strip(), operated_by=operator.id)
        OperationLogRepository.create(db, user_id=operator.id, action="reject_content", target_type="content", target_id=content.id, message=f"驳回内容 {content.title}")
        db.commit()
        updated = ContentRepository.get_by_id(db, content.id)
        if not updated:
            raise ResourceNotFound("内容不存在")
        return content_to_read(updated, include_body=True)

    @staticmethod
    def approve(db: Session, content_id: int, comment: str, operator: User) -> ContentRead:
        return PublishService.approve_and_publish(db, content_id, operator, comment)
