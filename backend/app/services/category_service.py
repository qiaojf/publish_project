from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFound
from app.db.base import utc_now
from app.db.models.category import Category
from app.db.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.operation_log_repository import OperationLogRepository
from app.schemas.category import CategoryPayload, CategoryRead, CategoryStatusUpdate


class CategoryService:
    @staticmethod
    def list(db: Session, current_user: User, *, include_disabled: bool) -> list[CategoryRead]:
        enabled_only = current_user.role != "admin" or not include_disabled
        return [CategoryRead.model_validate(item) for item in CategoryRepository.list(db, enabled_only=enabled_only)]

    @staticmethod
    def require_enabled(db: Session, name: str | None) -> Category:
        if not name:
            raise BusinessRuleError("请选择分类", 422)
        category = CategoryRepository.get_by_name(db, name)
        if not category:
            raise BusinessRuleError("所选分类不存在，请刷新分类列表", 422)
        if not category.enabled:
            raise BusinessRuleError("所选分类已禁用，请重新选择", 422)
        return category

    @staticmethod
    def create(db: Session, payload: CategoryPayload, operator: User) -> CategoryRead:
        if CategoryRepository.get_by_name(db, payload.name):
            raise BusinessRuleError("分类名称已存在")
        category = CategoryRepository.create(db, name=payload.name, enabled=payload.enabled, sort_order=payload.sort_order)
        OperationLogRepository.create(db, user_id=operator.id, action="create_category", target_type="category", target_id=category.id, message=f"创建分类 {category.name}")
        db.commit(); db.refresh(category)
        return CategoryRead.model_validate(category)

    @staticmethod
    def update(db: Session, category_id: int, payload: CategoryPayload, operator: User) -> CategoryRead:
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise ResourceNotFound("分类不存在")
        duplicate = CategoryRepository.get_by_name(db, payload.name)
        if duplicate and duplicate.id != category.id:
            raise BusinessRuleError("分类名称已存在")
        old_name = category.name
        if old_name != payload.name:
            CategoryRepository.rename_contents(db, old_name, payload.name)
        category.name = payload.name; category.enabled = payload.enabled; category.sort_order = payload.sort_order; category.updated_at = utc_now()
        OperationLogRepository.create(db, user_id=operator.id, action="update_category", target_type="category", target_id=category.id, message=f"更新分类 {category.name}")
        db.commit(); db.refresh(category)
        return CategoryRead.model_validate(category)

    @staticmethod
    def update_status(db: Session, category_id: int, payload: CategoryStatusUpdate, operator: User) -> CategoryRead:
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise ResourceNotFound("分类不存在")
        category.enabled = payload.enabled; category.updated_at = utc_now()
        action = "enable_category" if payload.enabled else "disable_category"
        OperationLogRepository.create(db, user_id=operator.id, action=action, target_type="category", target_id=category.id, message=f"{'启用' if payload.enabled else '禁用'}分类 {category.name}")
        db.commit(); db.refresh(category)
        return CategoryRead.model_validate(category)

    @staticmethod
    def delete(db: Session, category_id: int, operator: User) -> None:
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise ResourceNotFound("分类不存在")
        if CategoryRepository.content_count(db, category.name):
            raise BusinessRuleError("该分类已被内容使用，请改为禁用")
        OperationLogRepository.create(db, user_id=operator.id, action="delete_category", target_type="category", target_id=category.id, message=f"删除分类 {category.name}")
        db.delete(category); db.commit()
