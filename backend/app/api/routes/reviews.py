from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.core.constants import ContentType, ReviewStatus
from app.schemas.common import ApiResponse, PageResult
from app.schemas.content import ContentRead
from app.schemas.review import RejectRequest, ReviewComment, ReviewDetailRead
from app.services.review_service import ReviewService
from app.utils.datetime import end_of_day, start_of_day


router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=ApiResponse[PageResult[ContentRead]], summary="审核列表")
def list_reviews(
    db: DbSession, _admin: AdminUser, review_status: Annotated[ReviewStatus, Query(alias="status")] = ReviewStatus.PENDING,
    keyword: str | None = None, content_type: ContentType | None = None, category: str | None = None,
    submitted_by: str | None = None, date_from: date | None = None, date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[ContentRead]]:
    return ApiResponse(data=ReviewService.list(
        db, status=review_status.value, keyword=keyword, content_type=content_type.value if content_type else None,
        category=category, submitted_by=submitted_by, date_from=start_of_day(date_from), date_to=end_of_day(date_to),
        page=page, page_size=page_size,
    ))


@router.get("/{content_id}", response_model=ApiResponse[ReviewDetailRead], summary="审核详情")
def review_detail(content_id: int, db: DbSession, _admin: AdminUser) -> ApiResponse[ReviewDetailRead]:
    return ApiResponse(data=ReviewService.detail(db, content_id))


@router.post("/{content_id}/approve", response_model=ApiResponse[ContentRead], summary="审核通过并发布")
def approve(content_id: int, payload: ReviewComment, db: DbSession, admin: AdminUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=ReviewService.approve(db, content_id, payload.comment, admin), message="审核与发布流程已完成")


@router.post("/{content_id}/reject", response_model=ApiResponse[ContentRead], summary="驳回发布申请")
def reject(content_id: int, payload: RejectRequest, db: DbSession, admin: AdminUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=ReviewService.reject(db, content_id, payload.comment, admin), message="内容已驳回")
