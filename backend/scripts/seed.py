import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.constants import ContentType  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models.category import Category  # noqa: E402
from app.db.models.department import Department  # noqa: E402
from app.db.models.publish_target import PublishTarget  # noqa: E402
from app.db.models.user import User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


TARGETS = (("公司内容发布区", [item.value for item in ContentType], "content"),)
DEFAULT_CATEGORIES = ("制度规范", "产品资料", "销售方案", "培训材料", "品牌素材", "公共资源")
DEFAULT_DEPARTMENTS = ("管理部", "综合部")


def seed() -> None:
    settings = get_settings()
    users = (
        {"username": "admin", "password": settings.seed_admin_password, "name": "系统管理员", "department": "管理部", "role": "admin"},
        {"username": "employee", "password": settings.seed_employee_password, "name": "普通员工", "department": "综合部", "role": "employee"},
    )
    with SessionLocal() as db:
        for index, name in enumerate(DEFAULT_DEPARTMENTS, start=1):
            if not db.scalar(select(Department).where(Department.name == name)):
                db.add(Department(name=name, enabled=True, sort_order=index * 10))
        for index, name in enumerate(DEFAULT_CATEGORIES, start=1):
            if not db.scalar(select(Category).where(Category.name == name)):
                db.add(Category(name=name, enabled=True, sort_order=index * 10))
        for values in users:
            existing = db.scalar(select(User).where(User.username == values["username"]))
            if not existing:
                db.add(User(
                    username=values["username"], password_hash=hash_password(values["password"]),
                    name=values["name"], department=values["department"], role=values["role"], status="active",
                ))
        db.commit()
        admin = db.scalar(select(User).where(User.username == "admin"))
        if not admin:
            raise RuntimeError("Failed to seed admin user")
        for name, content_types, folder in TARGETS:
            existing = db.scalar(select(PublishTarget).where(PublishTarget.name == name))
            if not existing:
                publish_root = (settings.local_published_root / folder).resolve()
                publish_root.mkdir(parents=True, exist_ok=True)
                db.add(PublishTarget(
                    name=name, target_type="local", config={}, content_types=content_types, publish_root=str(publish_root),
                    base_url=f"{settings.local_published_base_url.rstrip('/')}/{folder}/",
                    enabled=True, created_by=admin.id,
                ))
        db.commit()
    print("Seed completed: admin, employee and development publish targets are ready.")


if __name__ == "__main__":
    seed()
