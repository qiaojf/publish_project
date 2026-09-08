from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models.category import Category
from app.db.models.department import Department
from app.db.models.user import User


class DepartmentRepository:
    @staticmethod
    def list(db: Session, *, enabled_only: bool = False) -> list[Department]:
        statement = select(Department)
        if enabled_only:
            statement = statement.where(Department.enabled.is_(True))
        return list(db.scalars(statement.order_by(Department.sort_order, Department.id)))

    @staticmethod
    def get_by_id(db: Session, department_id: int) -> Department | None:
        return db.get(Department, department_id)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Department | None:
        return db.scalar(select(Department).where(func.lower(Department.name) == name.lower()))

    @staticmethod
    def create(db: Session, **values: object) -> Department:
        department = Department(**values)
        db.add(department)
        db.flush()
        return department

    @staticmethod
    def usage_count(db: Session, name: str) -> int:
        user_count = db.scalar(
            select(func.count()).select_from(User).where(
                User.deleted_at.is_(None), func.lower(User.department) == name.lower(),
            )
        ) or 0
        category_count = db.scalar(
            select(func.count()).select_from(Category).where(func.lower(Category.department) == name.lower())
        ) or 0
        return user_count + category_count

    @staticmethod
    def rename_references(db: Session, old_name: str, new_name: str) -> None:
        db.execute(update(User).where(func.lower(User.department) == old_name.lower()).values(department=new_name))
        db.execute(update(Category).where(func.lower(Category.department) == old_name.lower()).values(department=new_name))
