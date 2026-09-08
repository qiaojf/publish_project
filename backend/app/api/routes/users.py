from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, DbSession
from app.core.constants import UserRole, UserStatus
from app.schemas.common import ApiResponse, PageResult
from app.schemas.user import UserCreate, UserRead, UserStatusUpdate, UserUpdate
from app.services.department_service import DepartmentService
from app.services.user_service import UserService


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=ApiResponse[PageResult[UserRead]], summary="用户列表")
def list_users(
    db: DbSession, _admin: AdminUser, keyword: str | None = None,
    role: UserRole | None = None, user_status: Annotated[UserStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[UserRead]]:
    return ApiResponse(data=UserService.list(db, keyword=keyword, role=role.value if role else None, status=user_status.value if user_status else None, page=page, page_size=page_size))


@router.post("", response_model=ApiResponse[UserRead], status_code=status.HTTP_201_CREATED, summary="新增用户")
def create_user(payload: UserCreate, db: DbSession, admin: AdminUser) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserService.create(db, payload, admin), message="用户已创建")


@router.get("/departments", response_model=ApiResponse[list[str]], summary="已有部门列表")
def list_departments(db: DbSession, _admin: AdminUser) -> ApiResponse[list[str]]:
    items = DepartmentService.list(db, _admin, include_disabled=False)
    return ApiResponse(data=[item.name for item in items])


@router.get("/{user_id}", response_model=ApiResponse[UserRead], summary="用户详情")
def get_user(user_id: int, db: DbSession, _admin: AdminUser) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserService.get(db, user_id))


@router.put("/{user_id}", response_model=ApiResponse[UserRead], summary="更新用户")
def update_user(user_id: int, payload: UserUpdate, db: DbSession, admin: AdminUser) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserService.update(db, user_id, payload, admin), message="用户已更新")


@router.patch("/{user_id}/status", response_model=ApiResponse[UserRead], summary="启用或禁用用户")
def update_user_status(user_id: int, payload: UserStatusUpdate, db: DbSession, admin: AdminUser) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserService.update_status(db, user_id, payload, admin), message="用户状态已更新")


@router.delete("/{user_id}", response_model=ApiResponse[dict[str, bool]], summary="逻辑删除用户")
def delete_user(user_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[dict[str, bool]]:
    UserService.delete(db, user_id, admin)
    return ApiResponse(data={"deleted": True}, message="用户已删除")
