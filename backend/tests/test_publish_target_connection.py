from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.publish_record import PublishRecord
from app.db.models.publish_target import PublishTarget
from tests.conftest import auth_headers


def test_connection_api_is_admin_only_and_creates_no_publish_record(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    employee = auth_headers(client, "employee")
    admin = auth_headers(client, "admin", "admin123")
    before = db.scalar(select(func.count()).select_from(PublishRecord)) or 0
    assert client.post(f"/api/publish-targets/{seeded['target']}/test", headers=employee).status_code == 403
    response = client.post(f"/api/publish-targets/{seeded['target']}/test", headers=admin)
    assert response.status_code == 200, response.text
    assert response.json()["data"] == {"connected": True}
    assert (db.scalar(select(func.count()).select_from(PublishRecord)) or 0) == before


def test_publish_target_get_never_returns_secret(
    client: TestClient, db: Session, seeded: dict[str, int], tmp_path: Path,
) -> None:
    target = PublishTarget(
        name="legacy unsafe row", target_type="dropbox", content_types=["file"],
        config={"folder_path": "/Company", "token": "must-not-leak", "nested": {"client_secret": "hidden"}},
        credential_ref="dropbox_company", publish_root=None, base_url=None, enabled=True,
        created_by=seeded["admin"],
    )
    db.add(target)
    db.commit()
    admin = auth_headers(client, "admin", "admin123")
    employee = auth_headers(client, "employee")
    admin_data = client.get(f"/api/publish-targets/{target.id}", headers=admin).json()["data"]
    assert "token" not in admin_data["config"]
    assert "client_secret" not in admin_data["config"].get("nested", {})
    employee_data = client.get("/api/publish-targets", headers=employee).json()["data"]
    visible = next(item for item in employee_data if item["id"] == target.id)
    assert set(visible) == {"id", "name", "target_type", "content_types", "enabled"}
