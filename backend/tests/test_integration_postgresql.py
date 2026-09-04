import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.content import Content
from app.db.models.operation_log import OperationLog
from app.db.models.publish_record import PublishRecord
from app.db.models.review_record import ReviewRecord
from app.db.models.user import User
from app.target_publishers.factory import TargetPublisherFactory
from tests.conftest import auth_headers, create_ppt


pytestmark = pytest.mark.integration


def test_authentication_and_role_guards(client: TestClient, db: Session, seeded: dict[str, int]) -> None:
    assert client.post("/api/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "disabled", "password": "employee123"}).status_code == 401
    employee_headers = auth_headers(client, "employee")
    assert client.get("/api/users", headers=employee_headers).status_code == 403
    assert client.get("/api/reviews", headers=employee_headers).status_code == 403
    assert client.get("/api/logs/operations", headers=employee_headers).status_code == 403
    assert client.get("/api/publish-records", headers=employee_headers).status_code == 403
    user = db.get(User, seeded["employee"])
    assert user is not None
    user.status = "disabled"
    db.commit()
    assert client.get("/api/auth/me", headers=employee_headers).status_code == 403


def test_database_constraints_and_defaults(db: Session, seeded: dict[str, int]) -> None:
    with pytest.raises(IntegrityError):
        db.add(User(username="admin", password_hash="x", name="Duplicate", role="admin", status="active"))
        db.commit()
    db.rollback()
    with pytest.raises(IntegrityError):
        db.add(User(username="bad-role", password_hash="x", name="Bad", role="superadmin", status="active"))
        db.commit()
    db.rollback()
    invalid = Content(title="Video", content_type="video", created_by=seeded["employee"])
    db.add(invalid)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    invalid_target = Content(title="Bad FK", content_type="ppt", created_by=seeded["employee"], publish_target_id=999999)
    db.add(invalid_target)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    valid = Content(title="Defaults", content_type="ppt", created_by=seeded["employee"], publish_target_id=seeded["target"])
    db.add(valid)
    db.commit()
    assert valid.review_status == "draft"
    assert valid.publish_status == "unpublished"


def test_employee_permissions_and_target_redaction(client: TestClient, db: Session, seeded: dict[str, int]) -> None:
    headers = auth_headers(client, "employee")
    own = create_ppt(client, seeded["target"], headers)
    preview = client.get(f"/api/contents/{own['id']}/preview", headers=headers)
    assert preview.status_code == 200
    assert preview.json()["data"]["preview_type"] == "file"
    source = client.get(f"/api/contents/{own['id']}/preview/file", headers=headers)
    assert source.status_code == 200 and source.content == b"fake pptx bytes"
    submit = client.post(f"/api/contents/{own['id']}/submit", headers=headers)
    assert submit.status_code == 200
    update_pending = client.put(
        f"/api/contents/{own['id']}",
        data={"title": "blocked", "content_type": "ppt", "publish_target_id": seeded["target"]},
        headers=headers,
    )
    assert update_pending.status_code == 409
    other = Content(title="Other", content_type="ppt", created_by=seeded["employee2"], publish_target_id=seeded["target"])
    db.add(other)
    db.commit()
    assert client.put(
        f"/api/contents/{other.id}",
        data={"title": "hijack", "content_type": "ppt", "publish_target_id": seeded["target"]},
        headers=headers,
    ).status_code == 403
    published = Content(
        title="Published", content_type="ppt", created_by=seeded["employee"],
        publish_target_id=seeded["target"], review_status="approved", publish_status="published",
    )
    db.add(published)
    db.commit()
    assert client.delete(f"/api/contents/{published.id}", headers=headers).status_code == 409
    targets = client.get("/api/publish-targets", headers=headers)
    assert targets.status_code == 200
    assert all("publish_root" not in item and "base_url" not in item for item in targets.json()["data"])
    assert client.post("/api/publish-targets", json={}, headers=headers).status_code == 403


def test_complete_reject_resubmit_publish_search_flow(client: TestClient, db: Session, seeded: dict[str, int]) -> None:
    employee = auth_headers(client, "employee")
    admin = auth_headers(client, "admin", "admin123")
    content = create_ppt(client, seeded["target"], employee, "完整发布流程")
    content_id = content["id"]
    assert content["review_status"] == "draft" and content["publish_status"] == "unpublished"
    assert client.post(f"/api/contents/{content_id}/submit", headers=employee).json()["data"]["review_status"] == "pending"
    hidden = client.get("/api/search", params={"keyword": "完整发布流程"}, headers=employee).json()["data"]
    assert hidden["total"] == 0
    assert client.post(f"/api/reviews/{content_id}/reject", json={"comment": "请补充数据来源"}, headers=admin).json()["data"]["review_status"] == "rejected"
    changed = client.put(
        f"/api/contents/{content_id}",
        data={"title": "完整发布流程（已修改）", "description": "已补充", "category": "培训材料", "content_type": "ppt", "publish_target_id": seeded["target"]},
        headers=employee,
    )
    assert changed.status_code == 200
    assert client.post(f"/api/contents/{content_id}/submit", headers=employee).status_code == 200
    approved = client.post(f"/api/reviews/{content_id}/approve", json={"comment": "审核通过"}, headers=admin)
    assert approved.status_code == 200, approved.text
    result = approved.json()["data"]
    assert result["review_status"] == "approved"
    assert result["publish_status"] == "published"
    assert result["view_url"]
    found = client.get("/api/search", params={"keyword": "完整发布流程"}, headers=employee).json()["data"]
    assert found["total"] == 1
    assert db.scalar(select(ReviewRecord).where(ReviewRecord.content_id == content_id, ReviewRecord.action == "submit"))
    assert db.scalar(select(ReviewRecord).where(ReviewRecord.content_id == content_id, ReviewRecord.action == "reject"))
    assert db.scalar(select(ReviewRecord).where(ReviewRecord.content_id == content_id, ReviewRecord.action == "approve"))
    publish_record = db.scalar(select(PublishRecord).where(PublishRecord.content_id == content_id))
    assert publish_record and publish_record.status == "success"
    assert db.scalar(select(OperationLog).where(OperationLog.target_id == content_id, OperationLog.action == "submit_content"))
    operation_logs = client.get("/api/logs/operations", headers=admin).json()["data"]["items"]
    assert any(item["target"] == "完整发布流程（已修改）" for item in operation_logs if item["target_type"] == "content")
    assert any(item["target"] == "admin" for item in operation_logs if item["action"] == "login")


def test_publish_failure_and_republish_history(
    client: TestClient, db: Session, seeded: dict[str, int], monkeypatch: pytest.MonkeyPatch,
) -> None:
    employee = auth_headers(client, "employee")
    admin = auth_headers(client, "admin", "admin123")
    content = create_ppt(client, seeded["target"], employee, "发布失败重试")
    content_id = content["id"]
    client.post(f"/api/contents/{content_id}/submit", headers=employee)

    class FailingPublisher:
        def publish(self, _artifact, _target):
            with Session(bind=db.get_bind()) as observer:
                visible_content = observer.get(Content, content_id)
                visible_record = observer.scalar(
                    select(PublishRecord)
                    .where(PublishRecord.content_id == content_id)
                    .order_by(PublishRecord.id.desc())
                )
                assert visible_content and visible_content.publish_status == "publishing"
                assert visible_record and visible_record.status == "publishing"
            raise RuntimeError("simulated publisher failure")

    monkeypatch.setattr(TargetPublisherFactory, "create", classmethod(lambda cls, target_type: FailingPublisher()))
    failed = client.post(f"/api/reviews/{content_id}/approve", json={"comment": "审核通过"}, headers=admin)
    assert failed.status_code == 200
    assert failed.json()["data"]["review_status"] == "approved"
    assert failed.json()["data"]["publish_status"] == "failed"
    monkeypatch.undo()
    retried = client.post(f"/api/contents/{content_id}/republish", headers=admin)
    assert retried.status_code == 200, retried.text
    assert retried.json()["data"]["publish_status"] == "published"
    records = list(db.scalars(select(PublishRecord).where(PublishRecord.content_id == content_id).order_by(PublishRecord.id)))
    assert [record.status for record in records] == ["failed", "success"]
