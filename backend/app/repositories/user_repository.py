from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int, *, include_deleted: bool = False) -> User | None:
        statement = select(User).where(User.id == user_id)
        if not include_deleted:
            statement = statement.where(User.deleted_at.is_(None))
        return db.scalar(statement)

    @staticmethod
    def get_by_username(db: Session, username: str, *, include_deleted: bool = False) -> User | None:
        statement = select(User).where(User.username == username)
        if not include_deleted:
            statement = statement.where(User.deleted_at.is_(None))
        return db.scalar(statement)

    @staticmethod
    def list(
        db: Session, *, keyword: str | None, role: str | None, status: str | None, page: int, page_size: int
    ) -> tuple[list[User], int]:
        filters = [User.deleted_at.is_(None)]
        if keyword:
            term = f"%{keyword}%"
            filters.append(or_(User.username.ilike(term), User.name.ilike(term)))
        if role:
            filters.append(User.role == role)
        if status:
            filters.append(User.status == status)
        total = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
        items = list(db.scalars(select(User).where(*filters).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
        return items, total

    @staticmethod
    def create(db: Session, **values: object) -> User:
        user = User(**values)
        db.add(user)
        db.flush()
        return user

    @staticmethod
    def soft_delete(user: User) -> None:
        user.deleted_at = utc_now()
        user.updated_at = utc_now()
