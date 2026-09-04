from pathlib import Path

from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.local import LocalTargetPublisher


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
