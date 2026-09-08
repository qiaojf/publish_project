from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.content import Content
from tests.conftest import auth_headers


def _create_category(client: TestClient, headers: dict[str, str], name: str, scope: str, department: str | None = None) -> None:
    response = client.post(
        "/api/categories",
        json={
            "name": name,
            "enabled": True,
            "sort_order": 100,
            "visibility_scope": scope,
            "department": department,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text


def test_user_department_is_returned_and_available_to_category_configuration(
    client: TestClient, seeded: dict[str, int],
) -> None:
    admin = auth_headers(client, "admin", "admin123")
    created = client.post(
        "/api/users",
        json={
            "username": "legal-user",
            "name": "法务同事",
            "department": "法务部",
            "password": "legal123",
            "role": "employee",
            "status": "active",
        },
        headers=admin,
    )
    assert created.status_code == 201, created.text
    assert created.json()["data"]["department"] == "法务部"

    legal = auth_headers(client, "legal-user", "legal123")
    assert client.get("/api/auth/me", headers=legal).json()["data"]["department"] == "法务部"
    departments = client.get("/api/users/departments", headers=admin)
    assert departments.status_code == 200
    assert {"管理部", "销售部", "研发部", "法务部"}.issubset(set(departments.json()["data"]))


def test_department_visibility_requires_a_department(client: TestClient) -> None:
    admin = auth_headers(client, "admin", "admin123")
    response = client.post(
        "/api/categories",
        json={"name": "部门资料", "enabled": True, "sort_order": 10, "visibility_scope": "department"},
        headers=admin,
    )
    assert response.status_code == 422
    assert "必须选择所属部门" in response.json()["message"]


def test_published_content_visibility_applies_to_search_detail_and_preview(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    admin = auth_headers(client, "admin", "admin123")
    publisher = auth_headers(client, "employee", "employee123")
    research = auth_headers(client, "employee2", "employee123")
    outsider_response = client.post(
        "/api/users",
        json={
            "username": "finance-user",
            "name": "财务同事",
            "department": "财务部",
            "password": "finance123",
            "role": "employee",
            "status": "active",
        },
        headers=admin,
    )
    assert outsider_response.status_code == 201, outsider_response.text
    outsider = auth_headers(client, "finance-user", "finance123")
    _create_category(client, admin, "发布者私有", "publisher")
    _create_category(client, admin, "研发可见", "department", "研发部")
    _create_category(client, admin, "全员可见", "all")

    contents = [
        Content(
            title=title,
            category=category,
            content_type="ppt",
            created_by=seeded["employee"],
            publish_target_id=seeded["target"],
            review_status="approved",
            publish_status="published",
        )
        for title, category in (
            ("发布者私有内容", "发布者私有"),
            ("研发部门内容", "研发可见"),
            ("全员公开内容", "全员可见"),
        )
    ]
    db.add_all(contents)
    db.commit()
    for content in contents:
        db.refresh(content)

    def search_titles(headers: dict[str, str]) -> set[str]:
        response = client.get("/api/search", params={"page_size": 100}, headers=headers)
        assert response.status_code == 200, response.text
        return {item["title"] for item in response.json()["data"]["items"]}

    assert {item.title for item in contents}.issubset(search_titles(admin))
    assert {item.title for item in contents}.issubset(search_titles(publisher))
    research_titles = search_titles(research)
    assert "发布者私有内容" not in research_titles
    assert {"研发部门内容", "全员公开内容"}.issubset(research_titles)
    outsider_titles = search_titles(outsider)
    assert "发布者私有内容" not in outsider_titles
    assert "研发部门内容" not in outsider_titles
    assert "全员公开内容" in outsider_titles

    private, department, everyone = contents
    assert client.get(f"/api/contents/{private.id}", headers=research).status_code == 403
    assert client.get(f"/api/contents/{private.id}/preview", headers=research).status_code == 403
    assert client.get(f"/api/contents/{private.id}", headers=publisher).status_code == 200
    assert client.get(f"/api/contents/{private.id}", headers=admin).status_code == 200
    assert client.get(f"/api/contents/{department.id}", headers=research).status_code == 200
    assert client.get(f"/api/contents/{department.id}", headers=outsider).status_code == 403
    assert client.get(f"/api/contents/{everyone.id}", headers=research).status_code == 200


def test_unpublished_content_remains_private_to_creator_and_admin(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    employee = auth_headers(client, "employee", "employee123")
    other = auth_headers(client, "employee2", "employee123")
    admin = auth_headers(client, "admin", "admin123")
    content = Content(
        title="尚未发布的全员分类内容",
        category="制度规范",
        content_type="ppt",
        created_by=seeded["employee"],
        publish_target_id=seeded["target"],
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    assert client.get(f"/api/contents/{content.id}", headers=employee).status_code == 200
    assert client.get(f"/api/contents/{content.id}", headers=admin).status_code == 200
    assert client.get(f"/api/contents/{content.id}", headers=other).status_code == 403
