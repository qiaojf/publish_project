from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardRead
from app.services.dashboard_service import DashboardService


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=ApiResponse[DashboardRead], summary="当前角色工作台数据")
def dashboard(db: DbSession, current_user: CurrentUser) -> ApiResponse[DashboardRead]:
    return ApiResponse(data=DashboardService.get(db, current_user))
