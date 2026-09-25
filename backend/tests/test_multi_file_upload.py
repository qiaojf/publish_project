from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models.publish_target import PublishTarget
from tests.conftest import auth_headers


def test_multi_file_upload_lists_files_and_publishes_bundle(
    client: TestClient, db: Session, seeded: dict[str, int], tmp_path: Path,
) -> None:
    target = PublishTarget(
        name="文件发布区", target_type="local", config={}, content_types=["file"],
        publish_root=str(tmp_path / "published-files"), base_url="http://localhost/files/",
        enabled=True, created_by=seeded["admin"],
    )
    db.add(target)
    db.commit()
    employee = auth_headers(client, "employee")
    admin = auth_headers(client, "admin", "admin123")
    response = client.post(
        "/api/contents",
        data={
            "title": "多文件内容", "category": "测试", "content_type": "file",
            "publish_target_id": str(target.id), "file_paths": ["资料/readme.txt", "资料/data.csv"],
        },
        files=[
            ("files", ("readme.txt", b"new readme", "text/plain")),
            ("files", ("data.csv", b"a,b\n1,2", "text/csv")),
        ],
        headers=employee,
    )
    assert response.status_code == 201, response.text
    content = response.json()["data"]
    assert content["source_is_directory"] is True
    assert [item["relative_path"] for item in content["files"]] == ["资料/readme.txt", "资料/data.csv"]

    preview = client.get(f"/api/contents/{content['id']}/preview", headers=employee).json()["data"]
    assert preview["preview_type"] == "files"
    assert preview["content"] is None
    downloaded = client.get(
        f"/api/contents/{content['id']}/preview/files/资料/readme.txt", headers=employee,
    )
    assert downloaded.status_code == 200 and downloaded.content == b"new readme"

    assert client.post(f"/api/contents/{content['id']}/submit", headers=employee).status_code == 200
    published = client.post(
        f"/api/reviews/{content['id']}/approve", json={"comment": "通过"}, headers=admin,
    )
    assert published.status_code == 200, published.text
    result = published.json()["data"]
    assert result["publish_status"] == "publishing"
    db.expire_all()
    completed = client.get(f"/api/contents/{content['id']}", headers=admin).json()["data"]
    assert completed["publish_status"] == "published"
    output = next((tmp_path / "published-files").iterdir())
    page = (output / "index.html").read_text(encoding="utf-8")
    assert "资料/readme.txt" in page and "资料/data.csv" in page


def test_instagram_video_content_accepts_exactly_one_video(
    client: TestClient, db: Session, seeded: dict[str, int],
) -> None:
    target = PublishTarget(
        name="公司 Instagram",
        target_type="instagram",
        config={
            "ig_user_id": "17841400000000000",
            "api_version": "v23.0",
            "media_base_url": "https://publish.example.com/local-published/_instagram/",
        },
        content_types=["video"],
        credential_ref="instagram_company",
        enabled=True,
        created_by=seeded["admin"],
    )
    db.add(target)
    db.commit()
    employee = auth_headers(client, "employee")
    data = {
        "title": "新品视频",
        "category": "测试",
        "content_type": "video",
        "publish_target_id": str(target.id),
    }

    multiple = client.post(
        "/api/contents",
        data={**data, "file_paths": ["part-1.mp4", "part-2.mp4"]},
        files=[
            ("files", ("part-1.mp4", b"video-1", "video/mp4")),
            ("files", ("part-2.mp4", b"video-2", "video/mp4")),
        ],
        headers=employee,
    )
    assert multiple.status_code == 422
    assert "MP4 或 MOV" in multiple.json()["message"]

    single = client.post(
        "/api/contents",
        data={**data, "file_paths": ["launch.mp4"]},
        files=[("files", ("launch.mp4", b"video", "video/mp4"))],
        headers=employee,
    )
    assert single.status_code == 201, single.text
    assert single.json()["data"]["content_type"] == "video"
    assert single.json()["data"]["files"][0]["relative_path"] == "launch.mp4"
