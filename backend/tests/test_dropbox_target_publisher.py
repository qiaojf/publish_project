from pathlib import Path

import httpx
import pytest

from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.dropbox import DropboxTargetPublisher


def make_target() -> PublishTarget:
    return PublishTarget(
        id=5, name="dropbox", target_type="dropbox", content_types=["file"],
        config={"folder_path": "/Company/Published/"}, credential_ref="dropbox_company",
        publish_root=None, base_url=None, enabled=True, created_by=1,
    )


def make_artifact(tmp_path: Path) -> PublishArtifact:
    root = tmp_path / "51-bundle"
    root.mkdir()
    (root / "index.html").write_text("bundle", encoding="utf-8")
    return PublishArtifact(root, "index.html", "file", True)


def test_dropbox_packages_directory_and_uploads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN", "token")
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        return httpx.Response(200, json={"id": "dropbox-item", "path_display": "/Company/Published/51-bundle.zip"})

    result = DropboxTargetPublisher(httpx.MockTransport(handler)).publish(make_artifact(tmp_path), make_target())
    assert "/2/files/upload" in requests
    assert result.remote_path == "/Company/Published/51-bundle.zip"
    assert result.publish_url == "https://www.dropbox.com/home/Company/Published?preview=51-bundle.zip"


def test_dropbox_single_file_keeps_original_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN", "token")
    source = tmp_path / "report.pdf"
    source.write_bytes(b"pdf")

    result = DropboxTargetPublisher(
        httpx.MockTransport(lambda _request: httpx.Response(200, json={"id": "dropbox-item"})),
    ).publish(PublishArtifact(source, source.name, "pdf", False), make_target())

    assert result.remote_path == "/Company/Published/report.pdf"
    assert result.publish_url == "https://www.dropbox.com/home/Company/Published?preview=report.pdf"


def test_dropbox_large_file_uses_upload_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN", "token")
    requests: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path.endswith("/start"): return httpx.Response(200, json={"session_id": "session"})
        return httpx.Response(200, json={"id": "dropbox-large"})

    publisher = DropboxTargetPublisher(httpx.MockTransport(handler))
    publisher.simple_upload_limit = 1
    result = publisher.publish(make_artifact(tmp_path), make_target())
    assert result.external_id == "dropbox-large"
    assert any(path.endswith("/upload_session/start") for path in requests)
    assert any(path.endswith("/upload_session/finish") for path in requests)


def test_dropbox_retries_rate_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN", "token")
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1: return httpx.Response(429)
        return httpx.Response(200, json={"id": "after-retry"})

    result = DropboxTargetPublisher(httpx.MockTransport(handler)).publish(make_artifact(tmp_path), make_target())
    assert result.external_id == "after-retry"
    assert attempts == 2
