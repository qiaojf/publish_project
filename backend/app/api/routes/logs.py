from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.schemas.common import ApiResponse, PageResult
from app.schemas.publish_record import OperationLogRead
from app.services.log_service import LogService
from app.utils.datetime import end_of_day, start_of_day


router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/operations", response_model=ApiResponse[PageResult[OperationLogRead]], summary="操作日志列表")
def operation_logs(
    db: DbSession, _admin: AdminUser, user_id: int | None = None, action: str | None = None,
    date_from: date | None = None, date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[OperationLogRead]]:
    return ApiResponse(data=LogService.operation_logs(
        db, user_id=user_id, action=action, date_from=start_of_day(date_from),
        date_to=end_of_day(date_to), page=page, page_size=page_size,
    ))
