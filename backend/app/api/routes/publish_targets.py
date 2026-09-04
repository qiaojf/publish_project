from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.publish_target import (
    PublishTargetAdminRead,
    PublishTargetConnectionRead,
    PublishTargetEmployeeRead,
    PublishTargetPayload,
    PublishTargetStatusUpdate,
)
from app.services.publish_target_service import PublishTargetService


router = APIRouter(prefix="/publish-targets", tags=["Publish Targets"])
TargetRead = PublishTargetAdminRead | PublishTargetEmployeeRead


@router.get("", response_model=ApiResponse[list[TargetRead]], summary="发布目标列表（按角色脱敏）")
def list_targets(db: DbSession, current_user: CurrentUser) -> ApiResponse[list[TargetRead]]:
    return ApiResponse(data=PublishTargetService.list(db, current_user))


@router.post("", response_model=ApiResponse[PublishTargetAdminRead], status_code=status.HTTP_201_CREATED, summary="新增发布目标")
def create_target(payload: PublishTargetPayload, db: DbSession, admin: AdminUser) -> ApiResponse[PublishTargetAdminRead]:
    return ApiResponse(data=PublishTargetService.create(db, payload, admin), message="发布目标已创建")


@router.get("/{target_id}", response_model=ApiResponse[PublishTargetAdminRead], summary="发布目标详情")
def get_target(target_id: int, db: DbSession, _admin: AdminUser) -> ApiResponse[PublishTargetAdminRead]:
    return ApiResponse(data=PublishTargetService.get_admin(db, target_id))


@router.put("/{target_id}", response_model=ApiResponse[PublishTargetAdminRead], summary="更新发布目标")
def update_target(target_id: int, payload: PublishTargetPayload, db: DbSession, admin: AdminUser) -> ApiResponse[PublishTargetAdminRead]:
    return ApiResponse(data=PublishTargetService.update(db, target_id, payload, admin), message="发布目标已更新")


@router.patch("/{target_id}/status", response_model=ApiResponse[PublishTargetAdminRead], summary="启用或禁用发布目标")
def update_target_status(target_id: int, payload: PublishTargetStatusUpdate, db: DbSession, admin: AdminUser) -> ApiResponse[PublishTargetAdminRead]:
    return ApiResponse(data=PublishTargetService.update_status(db, target_id, payload, admin), message="发布目标状态已更新")


@router.post("/{target_id}/test", response_model=ApiResponse[PublishTargetConnectionRead], summary="测试发布目标连接")
def test_target_connection(
    target_id: int, db: DbSession, admin: AdminUser,
) -> ApiResponse[PublishTargetConnectionRead]:
    return ApiResponse(
        data=PublishTargetService.test_connection(db, target_id, admin),
        message="连接成功",
    )


@router.delete("/{target_id}", response_model=ApiResponse[dict[str, bool]], summary="删除未使用的发布目标")
def delete_target(target_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[dict[str, bool]]:
    PublishTargetService.delete(db, target_id, admin)
    return ApiResponse(data={"deleted": True}, message="发布目标已删除")
