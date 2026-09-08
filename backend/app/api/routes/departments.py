from fastapi import APIRouter, status

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.common import ApiResponse
from app.schemas.department import DepartmentPayload, DepartmentRead, DepartmentStatusUpdate
from app.services.department_service import DepartmentService


router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=ApiResponse[list[DepartmentRead]], summary="部门列表")
def list_departments(
    db: DbSession, current_user: CurrentUser, include_disabled: bool = False,
) -> ApiResponse[list[DepartmentRead]]:
    return ApiResponse(data=DepartmentService.list(db, current_user, include_disabled=include_disabled))


@router.post("", response_model=ApiResponse[DepartmentRead], status_code=status.HTTP_201_CREATED, summary="新增部门")
def create_department(
    payload: DepartmentPayload, db: DbSession, admin: AdminUser,
) -> ApiResponse[DepartmentRead]:
    return ApiResponse(data=DepartmentService.create(db, payload, admin), message="部门已创建")


@router.put("/{department_id}", response_model=ApiResponse[DepartmentRead], summary="更新部门")
def update_department(
    department_id: int, payload: DepartmentPayload, db: DbSession, admin: AdminUser,
) -> ApiResponse[DepartmentRead]:
    return ApiResponse(data=DepartmentService.update(db, department_id, payload, admin), message="部门已更新")


@router.patch("/{department_id}/status", response_model=ApiResponse[DepartmentRead], summary="启用或禁用部门")
def update_department_status(
    department_id: int, payload: DepartmentStatusUpdate, db: DbSession, admin: AdminUser,
) -> ApiResponse[DepartmentRead]:
    return ApiResponse(data=DepartmentService.update_status(db, department_id, payload, admin), message="部门状态已更新")


@router.delete("/{department_id}", response_model=ApiResponse[dict[str, bool]], summary="删除部门")
def delete_department(department_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[dict[str, bool]]:
    DepartmentService.delete(db, department_id, admin)
    return ApiResponse(data={"deleted": True}, message="部门已删除")
