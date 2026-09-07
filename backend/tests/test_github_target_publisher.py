import base64
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from app.core.exceptions import PublishAuthenticationError, PublishTimeoutError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.github import GitHubTargetPublisher


def make_target(target_type: str = "github") -> PublishTarget:
    config = {"owner": "company", "repo": "content", "branch": "main", "repo_path": "published"}
    if target_type == "github_pages": config["base_url"] = "https://company.github.io/content/"
    return PublishTarget(
        id=3, name=target_type, target_type=target_type, content_types=["file"], config=config,
        credential_ref="github_company", publish_root=None, base_url=None, enabled=True, created_by=1,
    )


def make_transport(state: dict[str, int] | None = None) -> httpx.MockTransport:
    counters = state if state is not None else {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        counters[path] = counters.get(path, 0) + 1
        if request.method == "GET" and path.endswith("/repos/company/content"):
            return httpx.Response(200, json={"permissions": {"push": True}})
        if request.method == "GET" and path.endswith("/repos/company/content/pages"):
            return httpx.Response(200, json={
                "status": "built", "build_type": "legacy",
                "html_url": "https://company.github.io/content/",
                "source": {"branch": "main", "path": "/"},
            })
        if request.method == "GET" and path.endswith("/repos/company/content/pages/builds/latest"):
            return httpx.Response(200, json={"status": "built", "commit": "new-commit"})
        if request.method == "GET" and "/git/ref/heads/" in path:
            return httpx.Response(200, json={"object": {"sha": "head"}})
        if request.method == "GET" and path.endswith("/git/commits/head"):
            return httpx.Response(200, json={"tree": {"sha": "base-tree"}})
        if request.method == "GET" and path.endswith("/git/trees/base-tree"):
            return httpx.Response(200, json={"tree": []})
        if request.method == "POST" and path.endswith("/git/blobs"):
            return httpx.Response(201, json={"sha": f"blob-{counters[path]}"})
        if request.method == "POST" and path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "new-tree"})
        if request.method == "POST" and path.endswith("/git/commits"):
            return httpx.Response(201, json={"sha": "new-commit"})
        if request.method == "PATCH" and "/git/refs/heads/" in path:
            return httpx.Response(200, json={"object": {"sha": "new-commit"}})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def make_artifact(tmp_path: Path, content_type: str = "file") -> PublishArtifact:
    root = tmp_path / "31-demo"
    root.mkdir()
    (root / "index.html").write_text("demo", encoding="utf-8")
    return PublishArtifact(root, "index.html", content_type, True)


def test_github_target_commits_artifact_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "not-logged")
    result = GitHubTargetPublisher(make_transport()).publish(make_artifact(tmp_path), make_target())
    assert result.external_id == "new-commit"
    assert result.publish_url == "https://github.com/company/content/tree/main/published/31-demo"
    assert result.remote_path == "company/content:main/published/31-demo"


def test_github_target_uses_lfs_for_oversized_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "lfs-token")
    monkeypatch.setattr(GitHubTargetPublisher, "regular_blob_limit_bytes", 3)
    uploaded = bytearray()
    blobs: list[bytes] = []
    content = b"demo"
    oid = hashlib.sha256(content).hexdigest()

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path.endswith("/info/lfs/objects/batch"):
            payload = json.loads(request.content)
            assert payload["objects"] == [{"oid": oid, "size": len(content)}]
            return httpx.Response(200, json={"objects": [{"oid": oid, "size": len(content), "actions": {
                "upload": {"href": "https://uploads.github.test/lfs/object"},
                "verify": {"href": "https://uploads.github.test/lfs/verify"},
            }}]})
        if request.method == "PUT" and path == "/lfs/object":
            uploaded.extend(request.read())
            return httpx.Response(200)
        if request.method == "POST" and path == "/lfs/verify":
            return httpx.Response(200)
        if request.method == "GET" and "/git/ref/heads/" in path:
            return httpx.Response(200, json={"object": {"sha": "head"}})
        if request.method == "GET" and path.endswith("/git/commits/head"):
            return httpx.Response(200, json={"tree": {"sha": "base-tree"}})
        if request.method == "GET" and path.endswith("/git/trees/base-tree"):
            return httpx.Response(200, json={"tree": []})
        if request.method == "POST" and path.endswith("/git/blobs"):
            blobs.append(base64.b64decode(json.loads(request.content)["content"]))
            return httpx.Response(201, json={"sha": f"blob-{len(blobs)}"})
        if request.method == "POST" and path.endswith("/git/trees"):
            return httpx.Response(201, json={"sha": "new-tree"})
        if request.method == "POST" and path.endswith("/git/commits"):
            return httpx.Response(201, json={"sha": "new-commit"})
        if request.method == "PATCH" and "/git/refs/heads/" in path:
            return httpx.Response(200, json={"object": {"sha": "new-commit"}})
        return httpx.Response(404)

    result = GitHubTargetPublisher(httpx.MockTransport(handler)).publish(make_artifact(tmp_path), make_target())
    assert result.external_id == "new-commit"
    assert bytes(uploaded) == content
    assert any(f"oid sha256:{oid}".encode() in blob for blob in blobs)
    assert any(b"filter=lfs" in blob for blob in blobs)


def test_github_connection_retries_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        if request.url.path.endswith("/repos/company/content"):
            attempts += 1
            if attempts < 3: return httpx.Response(500)
            return httpx.Response(200, json={"permissions": {"push": True}})
        return httpx.Response(200, json={"object": {"sha": "head"}})

    assert GitHubTargetPublisher(httpx.MockTransport(handler)).test_connection(make_target()) is True
    assert attempts == 3


def test_github_authentication_error_does_not_expose_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token-value")
    transport = httpx.MockTransport(lambda _request: httpx.Response(401, text="token-value"))
    with pytest.raises(PublishAuthenticationError) as exc:
        GitHubTargetPublisher(transport).test_connection(make_target())
    assert "token-value" not in str(exc.value)


def test_github_timeout_is_retried_and_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("internal timeout detail", request=request)

    with pytest.raises(PublishTimeoutError, match="GitHub 检查仓库超时"):
        GitHubTargetPublisher(httpx.MockTransport(handler)).test_connection(make_target())
    assert attempts == 3
