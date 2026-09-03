from sqlalchemy.orm import Session

from app.core.constants import PublishRecordStatus, PublishStatus, ReviewAction, ReviewStatus
from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.db.base import utc_now
from app.db.models.content import Content
from app.db.models.publish_record import PublishRecord
from app.db.models.user import User
from app.publishers.factory import PublisherFactory
from app.repositories.content_repository import ContentRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.repositories.publish_record_repository import PublishRecordRepository
from app.repositories.publish_target_repository import PublishTargetRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.content import ContentRead
from app.services.publish_target_service import PublishTargetService
from app.services.serializers import content_to_read


class PublishService:
    @staticmethod
    def _validate_target(db: Session, content: Content):
        target = PublishTargetRepository.get_by_id(db, content.publish_target_id) if content.publish_target_id else None
        PublishTargetService.validate_for_content(target, content.content_type)
        return target

    @classmethod
    def approve_and_publish(cls, db: Session, content_id: int, operator: User, comment: str) -> ContentRead:
        content = ContentRepository.get_for_update(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        if content.review_status != ReviewStatus.PENDING.value:
            raise BusinessRuleError("该内容当前不在待审核状态")
        record = cls._initialize(db, content, operator, action="approve_content", review_action=True, comment=comment)
        return cls._execute(db, record.id)

    @classmethod
    def direct_publish(cls, db: Session, content_id: int, operator: User) -> ContentRead:
        content = ContentRepository.get_for_update(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        if content.publish_status == PublishStatus.PUBLISHING.value:
            raise BusinessRuleError("内容正在发布，请勿重复提交")
        record = cls._initialize(db, content, operator, action="publish_content", review_action=True, comment="管理员直接发布")
        return cls._execute(db, record.id)

    @classmethod
    def republish(cls, db: Session, content_id: int, operator: User) -> ContentRead:
        content = ContentRepository.get_for_update(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        if content.publish_status == PublishStatus.PUBLISHING.value:
            raise BusinessRuleError("内容正在发布，请勿重复提交")
        if content.review_status != ReviewStatus.APPROVED.value or content.publish_status != PublishStatus.FAILED.value:
            raise BusinessRuleError("仅审核通过且发布失败的内容可以重新发布")
        record = cls._initialize(db, content, operator, action="republish_content", review_action=False, comment=None)
        return cls._execute(db, record.id)

    @classmethod
    def _initialize(
        cls, db: Session, content: Content, operator: User, *, action: str, review_action: bool, comment: str | None,
    ) -> PublishRecord:
        target = cls._validate_target(db, content)
        assert target is not None
        from_status = content.review_status
        content.review_status = ReviewStatus.APPROVED.value
        content.publish_status = PublishStatus.PUBLISHING.value
        content.updated_at = utc_now()
        if review_action:
            ReviewRepository.create_record(
                db, content_id=content.id, action=ReviewAction.APPROVE.value, from_status=from_status,
                to_status=ReviewStatus.APPROVED.value, comment=comment, operated_by=operator.id,
            )
        record = PublishRecordRepository.create(
            db, content_id=content.id, publish_target_id=target.id, status=PublishRecordStatus.PUBLISHING.value,
            source_path=content.source_file_path, triggered_by=operator.id, started_at=utc_now(),
        )
        OperationLogRepository.create(db, user_id=operator.id, action=action, target_type="content", target_id=content.id, message=f"{action} {content.title}")
        db.commit()
        return record

    @classmethod
    def _execute(cls, db: Session, record_id: int) -> ContentRead:
        record = PublishRecordRepository.get_by_id(db, record_id)
        if not record:
            raise ResourceNotFound("发布记录不存在")
        content_id = record.content_id
        # End the relationship-loading read transaction before touching the filesystem.
        # SessionLocal keeps loaded values available because expire_on_commit=False.
        db.commit()
        try:
            publisher = PublisherFactory.create(record.content.content_type)
            result = publisher.publish(record.content, record.publish_target)
            record.status = PublishRecordStatus.SUCCESS.value
            record.output_path = result.output_path
            record.publish_url = result.view_url
            record.message = "发布成功"
            record.error_message = None
            record.finished_at = utc_now()
            record.content.publish_status = PublishStatus.PUBLISHED.value
            record.content.view_url = result.view_url
            record.content.published_at = utc_now()
            record.content.updated_at = utc_now()
            db.commit()
        except Exception as exc:
            db.rollback()
            failed_record = PublishRecordRepository.get_by_id(db, record_id)
            if not failed_record:
                raise
            failed_record.status = PublishRecordStatus.FAILED.value
            failed_record.error_message = str(exc)[:4000] or exc.__class__.__name__
            failed_record.finished_at = utc_now()
            failed_record.content.review_status = ReviewStatus.APPROVED.value
            failed_record.content.publish_status = PublishStatus.FAILED.value
            failed_record.content.updated_at = utc_now()
            db.commit()
        content = ContentRepository.get_by_id(db, content_id)
        if not content:
            raise ResourceNotFound("内容不存在")
        return content_to_read(content, include_body=True)
