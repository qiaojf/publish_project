from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.constants import ContentType
from app.schemas.common import ApiResponse, PageResult
from app.schemas.content import ContentRead
from app.services.search_service import SearchService
from app.utils.datetime import end_of_day, start_of_day


router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=ApiResponse[PageResult[ContentRead]], summary="检索已发布内容")
def search(
    db: DbSession, current_user: CurrentUser, keyword: str | None = None,
    content_type: ContentType | None = None, category: str | None = None,
    date_from: date | None = None, date_to: date | None = None,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[ContentRead]]:
    return ApiResponse(data=SearchService.search(
        db, current_user, keyword=keyword, content_type=content_type.value if content_type else None,
        category=category, date_from=start_of_day(date_from), date_to=end_of_day(date_to),
        page=page, page_size=page_size,
    ))
