from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_health_requires_the_application_schema(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_health_reports_a_missing_categories_table(client: TestClient, db: Session) -> None:
    db.execute(text("DROP TABLE categories"))
    db.commit()

    response = client.get("/api/health")

    assert response.status_code == 503
    assert "alembic upgrade head" in response.json()["message"]
