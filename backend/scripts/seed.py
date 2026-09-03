import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models.publish_target import PublishTarget  # noqa: E402
from app.db.models.user import User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


USERS = (
    {"username": "admin", "password": "admin123", "name": "系统管理员", "role": "admin"},
    {"username": "employee", "password": "employee123", "name": "普通员工", "role": "employee"},
)

TARGETS = (
    ("HTML 发布区", ["html", "dynamic"], "html"),
    ("PPT 发布区", ["ppt"], "ppt"),
    ("PDF 发布区", ["pdf"], "pdf"),
    ("文档发布区", ["word", "excel"], "documents"),
    ("图片发布区", ["image"], "images"),
    ("公共文件区", ["file"], "files"),
)


def seed() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        for values in USERS:
            existing = db.scalar(select(User).where(User.username == values["username"]))
            if not existing:
                db.add(User(
                    username=values["username"], password_hash=hash_password(values["password"]),
                    name=values["name"], role=values["role"], status="active",
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
                    name=name, content_types=content_types, publish_root=str(publish_root),
                    base_url=f"http://localhost:8000/local-published/{folder}/", enabled=True, created_by=admin.id,
                ))
        db.commit()
    print("Seed completed: admin, employee and development publish targets are ready.")


if __name__ == "__main__":
    seed()
