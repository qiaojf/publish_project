from pathlib import Path

import pytest

from app.core.exceptions import PublishTargetConfigurationError
from app.target_publishers.base import PublishArtifact
from app.target_publishers.github_pages import GitHubPagesTargetPublisher
from tests.test_github_target_publisher import make_artifact, make_target, make_transport


def test_github_pages_returns_pages_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    result = GitHubPagesTargetPublisher(make_transport()).publish(make_artifact(tmp_path), make_target("github_pages"))
    assert result.publish_url == "https://company.github.io/content/published/31-demo/"


def test_github_pages_rejects_dynamic_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    root = tmp_path / "32-dynamic"
    root.mkdir()
    (root / "index.html").write_text("dynamic", encoding="utf-8")
    artifact = PublishArtifact(root, "index.html", "dynamic", True)
    with pytest.raises(PublishTargetConfigurationError, match="不能发布到 GitHub Pages"):
        GitHubPagesTargetPublisher(make_transport()).publish(artifact, make_target("github_pages"))


def test_github_pages_rejects_file_that_would_require_lfs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    monkeypatch.setattr(GitHubPagesTargetPublisher, "regular_blob_limit_bytes", 3)
    with pytest.raises(PublishTargetConfigurationError, match="GitHub Pages 官方不支持 Git LFS"):
        GitHubPagesTargetPublisher(make_transport()).publish(make_artifact(tmp_path), make_target("github_pages"))


def test_github_pages_rejects_branch_different_from_pages_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_GITHUB_COMPANY_TOKEN", "token")
    target = make_target("github_pages")
    target.config = {**target.config, "branch": "other"}

    with pytest.raises(PublishTargetConfigurationError, match="发布分支为 main，当前目标配置为 other"):
        GitHubPagesTargetPublisher(make_transport()).test_connection(target)
