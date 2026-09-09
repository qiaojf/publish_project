from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.exceptions import PublishTargetConfigurationError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.local import LocalTargetPublisher
from app.utils import paths


def test_local_target_publishes_directory(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "build" / "12-demo"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "index.html").write_text("<h1>demo</h1>", encoding="utf-8")
    target = PublishTarget(
        id=1, name="local", target_type="local", config={}, content_types=["html"],
        publish_root=str(tmp_path / "published"), base_url="https://intranet.example/content/",
        enabled=True, created_by=1,
    )
    result = LocalTargetPublisher().publish(
        PublishArtifact(artifact_dir, "index.html", "html", True), target,
    )
    assert result.success is True
    assert result.publish_url == "https://intranet.example/content/12-demo/"
    assert Path(result.remote_path or "", "index.html").read_text(encoding="utf-8") == "<h1>demo</h1>"
    assert LocalTargetPublisher().test_connection(target) is True


def test_local_target_publishes_single_file_without_wrapper_directory(tmp_path: Path) -> None:
    source = tmp_path / "src-montage.png"
    source.write_bytes(b"png")
    published = tmp_path / "published"
    target = PublishTarget(
        id=4, name="local", target_type="local", config={}, content_types=["image"],
        publish_root=str(published), base_url="https://intranet.example/content/",
        enabled=True, created_by=1,
    )

    result = LocalTargetPublisher().publish(
        PublishArtifact(source, source.name, "image", False), target,
    )

    assert result.publish_url == "https://intranet.example/content/src-montage.png"
    assert result.remote_path == str(published / "src-montage.png")
    assert (published / "src-montage.png").read_bytes() == b"png"
    assert not (published / "src-montage.png" / "src-montage.png").exists()


def test_local_target_relative_root_matches_configured_url_mount(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mounted_root = tmp_path / "local-data" / "published"
    monkeypatch.setattr(paths, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        "app.target_publishers.local.get_settings",
        lambda: SimpleNamespace(
            local_published_root=mounted_root,
            local_published_base_url="http://localhost:8000/local-published",
        ),
    )
    target = PublishTarget(
        id=2, name="sales", target_type="local", config={}, content_types=["html"],
        publish_root="local-data/published/sales", base_url="http://localhost:8000/local-published/sales/",
        enabled=True, created_by=1,
    )
    assert LocalTargetPublisher().test_connection(target) is True
    assert (mounted_root / "sales").is_dir()


def test_local_target_rejects_mismatched_configured_url_mount(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.target_publishers.local.get_settings",
        lambda: SimpleNamespace(
            local_published_root=tmp_path / "served",
            local_published_base_url="http://localhost:8000/local-published",
        ),
    )
    target = PublishTarget(
        id=3, name="sales", target_type="local", config={}, content_types=["html"],
        publish_root=str(tmp_path / "not-served"), base_url="http://localhost:8000/local-published/sales/",
        enabled=True, created_by=1,
    )
    with pytest.raises(PublishTargetConfigurationError, match="发布根目录与 URL 根地址不匹配"):
        LocalTargetPublisher().test_connection(target)
