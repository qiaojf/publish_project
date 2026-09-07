from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.content import Content
from tests.conftest import auth_headers, create_ppt


def test_categories_are_configurable_and_rename_existing_content(client: TestClient, db: Session, seeded: dict[str, int]) -> None:
    admin = auth_headers(client, "admin", "admin123"); employee = auth_headers(client, "employee", "employee123")
    created_response = client.post("/api/categories", json={"name": "客户案例", "enabled": True, "sort_order": 15}, headers=admin)
    assert created_response.status_code == 201
    category_id = created_response.json()["data"]["id"]
    content = create_ppt(client, seeded["target"], employee, "分类重命名验证")
    model = db.get(Content, content["id"]); assert model is not None
    model.category = "客户案例"; db.commit()
    updated_response = client.put(f"/api/categories/{category_id}", json={"name": "成功案例", "enabled": True, "sort_order": 20}, headers=admin)
    assert updated_response.status_code == 200
    db.refresh(model); assert model.category == "成功案例"
    assert client.patch(f"/api/categories/{category_id}/status", json={"enabled": False}, headers=admin).status_code == 200
    assert all(item["name"] != "成功案例" for item in client.get("/api/categories", headers=employee).json()["data"])
    assert any(item["name"] == "成功案例" and not item["enabled"] for item in client.get("/api/categories?include_disabled=true", headers=admin).json()["data"])
    delete_response = client.delete(f"/api/categories/{category_id}", headers=admin)
    assert delete_response.status_code == 409
    assert "已被内容使用" in delete_response.json()["message"]


def test_content_rejects_unknown_or_disabled_category(client: TestClient, seeded: dict[str, int]) -> None:
    admin = auth_headers(client, "admin", "admin123"); employee = auth_headers(client, "employee", "employee123")
    created = client.post("/api/categories", json={"name": "停用分类", "enabled": False, "sort_order": 99}, headers=admin).json()["data"]
    for category, expected in (("不存在", "不存在"), (created["name"], "已禁用")):
        response = client.post("/api/contents", data={"title": "分类校验", "category": category, "content_type": "ppt", "publish_target_id": str(seeded["target"])}, files={"file": ("demo.pptx", b"data", "application/octet-stream")}, headers=employee)
        assert response.status_code == 422
        assert expected in response.json()["message"]
