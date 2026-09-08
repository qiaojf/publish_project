from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.db.base import utc_now
from app.db.models.department import Department
from app.db.models.user import User
from app.repositories.department_repository import DepartmentRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.department import DepartmentPayload, DepartmentRead, DepartmentStatusUpdate


class DepartmentService:
    @staticmethod
    def list(db: Session, current_user: User, *, include_disabled: bool) -> list[DepartmentRead]:
        enabled_only = current_user.role != "admin" or not include_disabled
        return [DepartmentRead.model_validate(item) for item in DepartmentRepository.list(db, enabled_only=enabled_only)]

    @staticmethod
    def require_enabled(db: Session, name: str | None) -> Department | None:
        if not name:
            return None
        department = DepartmentRepository.get_by_name(db, name)
        if not department:
            raise BusinessRuleError("所选部门不存在，请刷新部门列表", 422)
        if not department.enabled:
            raise BusinessRuleError("所选部门已禁用，请重新选择", 422)
        return department

    @staticmethod
    def create(db: Session, payload: DepartmentPayload, operator: User) -> DepartmentRead:
        if DepartmentRepository.get_by_name(db, payload.name):
            raise BusinessRuleError("部门名称已存在")
        department = DepartmentRepository.create(
            db, name=payload.name, enabled=payload.enabled, sort_order=payload.sort_order,
        )
        OperationLogRepository.create(
            db, user_id=operator.id, action="create_department", target_type="department",
            target_id=department.id, message=f"创建部门 {department.name}",
        )
        db.commit(); db.refresh(department)
        return DepartmentRead.model_validate(department)

    @staticmethod
    def update(db: Session, department_id: int, payload: DepartmentPayload, operator: User) -> DepartmentRead:
        department = DepartmentRepository.get_by_id(db, department_id)
        if not department:
            raise ResourceNotFound("部门不存在")
        duplicate = DepartmentRepository.get_by_name(db, payload.name)
        if duplicate and duplicate.id != department.id:
            raise BusinessRuleError("部门名称已存在")
        old_name = department.name
        if old_name != payload.name:
            DepartmentRepository.rename_references(db, old_name, payload.name)
        department.name = payload.name
        department.enabled = payload.enabled
        department.sort_order = payload.sort_order
        department.updated_at = utc_now()
        OperationLogRepository.create(
            db, user_id=operator.id, action="update_department", target_type="department",
            target_id=department.id, message=f"更新部门 {department.name}",
        )
        db.commit(); db.refresh(department)
        return DepartmentRead.model_validate(department)

    @staticmethod
    def update_status(
        db: Session, department_id: int, payload: DepartmentStatusUpdate, operator: User,
    ) -> DepartmentRead:
        department = DepartmentRepository.get_by_id(db, department_id)
        if not department:
            raise ResourceNotFound("部门不存在")
        department.enabled = payload.enabled
        department.updated_at = utc_now()
        action = "enable_department" if payload.enabled else "disable_department"
        OperationLogRepository.create(
            db, user_id=operator.id, action=action, target_type="department", target_id=department.id,
            message=f"{'启用' if payload.enabled else '禁用'}部门 {department.name}",
        )
        db.commit(); db.refresh(department)
        return DepartmentRead.model_validate(department)

    @staticmethod
    def delete(db: Session, department_id: int, operator: User) -> None:
        department = DepartmentRepository.get_by_id(db, department_id)
        if not department:
            raise ResourceNotFound("部门不存在")
        if DepartmentRepository.usage_count(db, department.name):
            raise BusinessRuleError("该部门已被用户或分类使用，请改为禁用")
        OperationLogRepository.create(
            db, user_id=operator.id, action="delete_department", target_type="department",
            target_id=department.id, message=f"删除部门 {department.name}",
        )
        db.delete(department); db.commit()
