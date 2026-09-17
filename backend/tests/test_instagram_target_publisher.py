from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs

import httpx
import pytest

from app.core.config import get_settings
from app.core.exceptions import PublishTargetConfigurationError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.instagram import InstagramTargetPublisher


IG_USER_ID = "17841400000000000"


def make_target(*, ig_user_id: str = IG_USER_ID) -> PublishTarget:
    return PublishTarget(
        id=8,
        name="公司 Instagram",
        target_type="instagram",
        content_types=["video"],
        config={
            "ig_user_id": ig_user_id,
            "api_version": "v23.0",
            "media_base_url": "https://publish.example.com/local-published/_instagram/",
        },
        credential_ref="instagram_company",
        publish_root=None,
        base_url=None,
        enabled=True,
        created_by=1,
    )


def make_video(tmp_path: Path) -> PublishArtifact:
    source = tmp_path / "launch-video.mp4"
    source.write_bytes(b"fake-video-data")
    return PublishArtifact(
        source,
        source.name,
        "video",
        False,
        ((source, source.name),),
        "新品发布",
        "公司新品介绍",
    )


def test_instagram_connection_checks_configured_account(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_INSTAGRAM_COMPANY_ACCESS_TOKEN", "secret-token")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret-token"
        assert request.url.params["fields"] == "id,username"
        return httpx.Response(200, json={"id": IG_USER_ID, "username": "company", "account_type": "BUSINESS"})

    assert InstagramTargetPublisher(httpx.MockTransport(handler)).test_connection(make_target()) is True


def test_instagram_connection_rejects_account_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_INSTAGRAM_COMPANY_ACCESS_TOKEN", "secret-token")
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={"id": "999"}))
    with pytest.raises(PublishTargetConfigurationError, match="账号与配置"):
        InstagramTargetPublisher(transport).test_connection(make_target())


def test_instagram_publishes_reel_from_public_staged_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_INSTAGRAM_COMPANY_ACCESS_TOKEN", "secret-token")
    monkeypatch.setattr(get_settings(), "local_published_root", tmp_path / "published")
    monkeypatch.setattr(InstagramTargetPublisher, "status_poll_interval_seconds", 0)
    monkeypatch.setattr("app.target_publishers.instagram.uuid4", lambda: SimpleNamespace(hex="upload-123"))
    status_checks = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal status_checks
        assert request.headers["authorization"] == "Bearer secret-token"
        if request.method == "POST" and request.url.path.endswith(f"/{IG_USER_ID}/media"):
            body = parse_qs(request.content.decode())
            assert body == {
                "media_type": ["REELS"],
                "video_url": ["https://publish.example.com/local-published/_instagram/upload-123/launch-video.mp4"],
                "share_to_feed": ["true"],
                "caption": ["新品发布\n\n公司新品介绍"],
            }
            return httpx.Response(200, json={"id": "container-1"})
        if request.method == "GET" and request.url.path.endswith("/container-1"):
            status_checks += 1
            return httpx.Response(200, json={"status_code": "IN_PROGRESS" if status_checks == 1 else "FINISHED"})
        if request.method == "POST" and request.url.path.endswith(f"/{IG_USER_ID}/media_publish"):
            assert parse_qs(request.content.decode()) == {"creation_id": ["container-1"]}
            return httpx.Response(200, json={"id": "media-1"})
        if request.method == "GET" and request.url.path.endswith("/media-1"):
            return httpx.Response(200, json={"permalink": "https://www.instagram.com/reel/example/"})
        return httpx.Response(404)

    result = InstagramTargetPublisher(httpx.MockTransport(handler)).publish(make_video(tmp_path), make_target())

    assert status_checks == 2
    assert not (tmp_path / "published" / "_instagram" / "upload-123").exists()
    assert result.publish_url == "https://www.instagram.com/reel/example/"
    assert result.remote_path == "instagram:media-1"
    assert result.external_id == "media-1"


def test_instagram_reports_container_processing_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_INSTAGRAM_COMPANY_ACCESS_TOKEN", "secret-token")
    monkeypatch.setattr(get_settings(), "local_published_root", tmp_path / "published")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path.endswith(f"/{IG_USER_ID}/media"):
            return httpx.Response(200, json={"id": "container-1"})
        if request.method == "GET" and request.url.path.endswith("/container-1"):
            return httpx.Response(200, json={"status_code": "ERROR"})
        return httpx.Response(404)

    with pytest.raises(PublishUploadError, match="视频处理失败"):
        InstagramTargetPublisher(httpx.MockTransport(handler)).publish(make_video(tmp_path), make_target())


def test_instagram_rejects_non_video_artifact(tmp_path: Path) -> None:
    source = tmp_path / "document.pdf"
    source.write_bytes(b"pdf")
    artifact = PublishArtifact(source, source.name, "video", False, ((source, source.name),))
    with pytest.raises(PublishTargetConfigurationError, match="MP4 或 MOV"):
        InstagramTargetPublisher().validate_artifact(artifact)
