from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.models.category import Category
from app.db.models.publish_target import PublishTarget
from app.db.models.user import User
from app.db.session import get_db
from app.main import app


@pytest.fixture
def postgres_engine():
    settings = get_settings()
    assert settings.test_database_url.startswith("postgresql+psycopg://")
    assert settings.test_database_url != settings.database_url, "TEST_DATABASE_URL must not equal DATABASE_URL"
    engine = create_engine(settings.test_database_url, connect_args={"connect_timeout": 2}, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError:
        engine.dispose()
        pytest.skip("Isolated PostgreSQL TEST_DATABASE_URL is unavailable")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db(postgres_engine) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=postgres_engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def seeded(db: Session, tmp_path: Path) -> dict[str, int]:
    settings = get_settings()
    settings.source_storage_root = (tmp_path / "source").resolve()
    settings.build_storage_root = (tmp_path / "build").resolve()
    db.add_all([Category(name=name, enabled=True, sort_order=index * 10) for index, name in enumerate(("制度规范", "产品资料", "销售方案", "培训材料", "品牌素材", "公共资源", "测试"), start=1)])
    users = [
        User(username="admin", password_hash=hash_password("admin123"), name="系统管理员", role="admin", status="active"),
        User(username="employee", password_hash=hash_password("employee123"), name="普通员工", role="employee", status="active"),
        User(username="employee2", password_hash=hash_password("employee123"), name="其他员工", role="employee", status="active"),
        User(username="disabled", password_hash=hash_password("employee123"), name="禁用员工", role="employee", status="disabled"),
    ]
    db.add_all(users)
    db.flush()
    target = PublishTarget(
        name="PPT 发布区", target_type="local", config={}, content_types=["ppt"], publish_root=str(tmp_path / "published"),
        base_url="http://localhost:8000/local-published/ppt/", enabled=True, created_by=users[0].id,
    )
    db.add(target)
    db.commit()
    return {"admin": users[0].id, "employee": users[1].id, "employee2": users[2].id, "disabled": users[3].id, "target": target.id}


@pytest.fixture
def client(db: Session, seeded: dict[str, int]) -> Generator[TestClient, None, None]:
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(client: TestClient, username: str, password: str = "employee123") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['token']}"}


def create_ppt(client: TestClient, target_id: int, headers: dict[str, str], title: str = "测试演示文稿") -> dict:
    response = client.post(
        "/api/contents",
        data={"title": title, "description": "pytest 内容", "category": "培训材料", "content_type": "ppt", "publish_target_id": str(target_id)},
        files={"file": ("demo.pptx", b"fake pptx bytes", "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]
