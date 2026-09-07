from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.category import CategoryPayload, CategoryRead, CategoryStatusUpdate
from app.schemas.common import ApiResponse
from app.services.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=ApiResponse[list[CategoryRead]], summary="分类列表")
def list_categories(db: DbSession, current_user: CurrentUser, include_disabled: bool = False) -> ApiResponse[list[CategoryRead]]:
    return ApiResponse(data=CategoryService.list(db, current_user, include_disabled=include_disabled))


@router.post("", response_model=ApiResponse[CategoryRead], status_code=status.HTTP_201_CREATED, summary="新增分类")
def create_category(payload: CategoryPayload, db: DbSession, admin: AdminUser) -> ApiResponse[CategoryRead]:
    return ApiResponse(data=CategoryService.create(db, payload, admin), message="分类已创建")


@router.put("/{category_id}", response_model=ApiResponse[CategoryRead], summary="更新分类")
def update_category(category_id: int, payload: CategoryPayload, db: DbSession, admin: AdminUser) -> ApiResponse[CategoryRead]:
    return ApiResponse(data=CategoryService.update(db, category_id, payload, admin), message="分类已更新")


@router.patch("/{category_id}/status", response_model=ApiResponse[CategoryRead], summary="启用或禁用分类")
def update_category_status(category_id: int, payload: CategoryStatusUpdate, db: DbSession, admin: AdminUser) -> ApiResponse[CategoryRead]:
    return ApiResponse(data=CategoryService.update_status(db, category_id, payload, admin), message="分类状态已更新")


@router.delete("/{category_id}", response_model=ApiResponse[dict[str, bool]], summary="删除分类")
def delete_category(category_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[dict[str, bool]]:
    CategoryService.delete(db, category_id, admin)
    return ApiResponse(data={"deleted": True}, message="分类已删除")
