from pathlib import Path

import httpx
import pytest

from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.onedrive import OneDriveTargetPublisher


def make_target() -> PublishTarget:
    return PublishTarget(
        id=4, name="onedrive", target_type="onedrive", content_types=["pdf"],
        config={"tenant_id": "tenant", "client_id": "client", "drive_id": "drive", "folder_path": "/Company/Published/"},
        credential_ref="onedrive_company", publish_root=None, base_url=None, enabled=True, created_by=1,
    )


def make_artifact(tmp_path: Path) -> PublishArtifact:
    root = tmp_path / "41-document"
    root.mkdir()
    (root / "index.html").write_text("document", encoding="utf-8")
    return PublishArtifact(root, "index.html", "pdf", True)


def test_onedrive_packages_directory_and_returns_web_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET", "secret")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "login.microsoftonline.com": return httpx.Response(200, json={"access_token": "access"})
        if request.method == "PUT": return httpx.Response(201, json={"id": "item", "webUrl": "https://onedrive.example/item"})
        return httpx.Response(200, json={"id": "drive"})

    result = OneDriveTargetPublisher(httpx.MockTransport(handler)).publish(make_artifact(tmp_path), make_target())
    assert result.publish_url == "https://onedrive.example/item"
    assert result.remote_path == "/Company/Published/41-document.zip"


def test_onedrive_single_file_keeps_original_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET", "secret")
    source = tmp_path / "report.pdf"
    source.write_bytes(b"pdf")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "login.microsoftonline.com": return httpx.Response(200, json={"access_token": "access"})
        if request.method == "PUT": return httpx.Response(201, json={"id": "item", "webUrl": "https://onedrive.example/report"})
        return httpx.Response(200, json={"id": "drive"})

    result = OneDriveTargetPublisher(httpx.MockTransport(handler)).publish(
        PublishArtifact(source, source.name, "pdf", False), make_target(),
    )

    assert result.remote_path == "/Company/Published/report.pdf"


def test_onedrive_large_file_uses_upload_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET", "secret")
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.host == "login.microsoftonline.com": return httpx.Response(200, json={"access_token": "access"})
        if request.method == "POST": return httpx.Response(200, json={"uploadUrl": "https://upload.example/session"})
        return httpx.Response(201, json={"id": "large", "webUrl": "https://onedrive.example/large"})

    publisher = OneDriveTargetPublisher(httpx.MockTransport(handler))
    publisher.simple_upload_limit = 1
    result = publisher.publish(make_artifact(tmp_path), make_target())
    assert result.external_id == "large"
    assert any("createUploadSession" in call for call in calls)
    assert any(call.startswith("PUT /session") for call in calls)
