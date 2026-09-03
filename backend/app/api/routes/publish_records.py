from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.core.constants import ContentType, PublishRecordStatus
from app.schemas.common import ApiResponse, PageResult
from app.schemas.publish_record import PublishRecordRead
from app.services.log_service import LogService
from app.utils.datetime import end_of_day, start_of_day


router = APIRouter(prefix="/publish-records", tags=["Publish Records"])


@router.get("", response_model=ApiResponse[PageResult[PublishRecordRead]], summary="发布记录列表")
def list_publish_records(
    db: DbSession, _admin: AdminUser, content_id: int | None = None, keyword: str | None = None,
    record_status: Annotated[PublishRecordStatus | None, Query(alias="status")] = None,
    content_type: ContentType | None = None, date_from: date | None = None, date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[PublishRecordRead]]:
    return ApiResponse(data=LogService.publish_records(
        db, content_id=content_id, keyword=keyword, status=record_status.value if record_status else None,
        content_type=content_type.value if content_type else None, date_from=start_of_day(date_from),
        date_to=end_of_day(date_to), page=page, page_size=page_size,
    ))


@router.get("/{record_id}", response_model=ApiResponse[PublishRecordRead], summary="发布记录详情")
def get_publish_record(record_id: int, db: DbSession, _admin: AdminUser) -> ApiResponse[PublishRecordRead]:
    return ApiResponse(data=LogService.publish_record(db, record_id))
