from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models.category import Category
from app.db.models.content import Content


class CategoryRepository:
    @staticmethod
    def list(db: Session, *, enabled_only: bool = False) -> list[Category]:
        statement = select(Category)
        if enabled_only:
            statement = statement.where(Category.enabled.is_(True))
        return list(db.scalars(statement.order_by(Category.sort_order, Category.id)))

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Category | None:
        return db.get(Category, category_id)

    @staticmethod
    def get_by_name(db: Session, name: str) -> Category | None:
        return db.scalar(select(Category).where(func.lower(Category.name) == name.lower()))

    @staticmethod
    def create(db: Session, **values: object) -> Category:
        category = Category(**values)
        db.add(category)
        db.flush()
        return category

    @staticmethod
    def content_count(db: Session, name: str) -> int:
        return db.scalar(select(func.count()).select_from(Content).where(Content.category == name, Content.deleted_at.is_(None))) or 0

    @staticmethod
    def rename_contents(db: Session, old_name: str, new_name: str) -> None:
        db.execute(update(Content).where(Content.category == old_name).values(category=new_name))
