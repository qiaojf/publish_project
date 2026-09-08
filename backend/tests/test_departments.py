from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.models.category import Category
from app.db.models.user import User
from tests.conftest import auth_headers


def test_departments_are_configurable_and_rename_references(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    admin = auth_headers(client, "admin", "admin123")
    created = client.post(
        "/api/departments",
        json={"name": "客户成功部", "enabled": True, "sort_order": 15},
        headers=admin,
    )
    assert created.status_code == 201, created.text
    department_id = created.json()["data"]["id"]

    user = db.get(User, seeded["employee"])
    category = db.query(Category).filter(Category.name == "制度规范").one()
    assert user is not None
    user.department = "客户成功部"
    category.visibility_scope = "department"
    category.department = "客户成功部"
    db.commit()

    updated = client.put(
        f"/api/departments/{department_id}",
        json={"name": "客户体验部", "enabled": True, "sort_order": 20},
        headers=admin,
    )
    assert updated.status_code == 200, updated.text
    db.refresh(user); db.refresh(category)
    assert user.department == "客户体验部"
    assert category.department == "客户体验部"

    disabled = client.patch(
        f"/api/departments/{department_id}/status", json={"enabled": False}, headers=admin,
    )
    assert disabled.status_code == 200
    employee_list = client.get("/api/departments", headers=auth_headers(client, "employee"))
    assert all(item["name"] != "客户体验部" for item in employee_list.json()["data"])
    delete_response = client.delete(f"/api/departments/{department_id}", headers=admin)
    assert delete_response.status_code == 409
    assert "已被用户或分类使用" in delete_response.json()["message"]


def test_user_update_accepts_blank_password_and_keeps_existing_hash(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    admin = auth_headers(client, "admin", "admin123")
    user = db.get(User, seeded["employee"])
    assert user is not None
    original_hash = user.password_hash
    response = client.put(
        f"/api/users/{user.id}",
        json={
            "username": user.username,
            "name": "更新后的员工",
            "department": "销售部",
            "password": "",
            "role": "employee",
            "status": "active",
        },
        headers=admin,
    )
    assert response.status_code == 200, response.text
    db.refresh(user)
    assert user.password_hash == original_hash
    assert verify_password("employee123", user.password_hash)


def test_user_and_category_reject_unknown_or_disabled_departments(
    client: TestClient,
) -> None:
    admin = auth_headers(client, "admin", "admin123")
    created = client.post(
        "/api/departments",
        json={"name": "待停用部门", "enabled": False, "sort_order": 99},
        headers=admin,
    ).json()["data"]
    for index, (department, expected) in enumerate((("不存在部门", "不存在"), (created["name"], "已禁用")), start=1):
        user_response = client.post(
            "/api/users",
            json={
                "username": f"department-user-{index}", "name": "部门校验用户", "department": department,
                "password": "password123", "role": "employee", "status": "active",
            },
            headers=admin,
        )
        assert user_response.status_code == 422
        assert expected in user_response.json()["message"]
        category_response = client.post(
            "/api/categories",
            json={
                "name": f"分类-{department}", "enabled": True, "sort_order": 100,
                "visibility_scope": "department", "department": department,
            },
            headers=admin,
        )
        assert category_response.status_code == 422
        assert expected in category_response.json()["message"]
