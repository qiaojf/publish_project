from pathlib import Path

import paramiko
import pytest

from app.core.exceptions import PublishAuthenticationError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact
from app.target_publishers.sftp import SftpTargetPublisher


class FakeChannel:
    def settimeout(self, _value): pass


class FakeSftp:
    def __init__(self) -> None:
        self.directories = {"/", "/srv", "/srv/content"}
        self.uploads: list[tuple[str, str]] = []

    def get_channel(self): return FakeChannel()
    def stat(self, path):
        if path not in self.directories: raise OSError(path)
        return object()
    def mkdir(self, path): self.directories.add(path)
    def put(self, local, remote, confirm=True): self.uploads.append((local, remote))
    def close(self): pass


class FakeClient:
    def __init__(self, sftp: FakeSftp, error: Exception | None = None) -> None:
        self.sftp = sftp
        self.error = error

    def load_system_host_keys(self): pass
    def connect(self, **_kwargs):
        if self.error: raise self.error
    def open_sftp(self): return self.sftp
    def close(self): pass


def make_target() -> PublishTarget:
    return PublishTarget(
        id=2, name="sftp", target_type="sftp", content_types=["file"], publish_root=None, base_url=None,
        config={"host": "server", "port": 22, "username": "publisher", "remote_root": "/srv/content", "base_url": "https://internal.example/content/"},
        credential_ref="sftp_internal", enabled=True, created_by=1,
    )


def test_sftp_target_uploads_recursively(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD", "not-logged")
    root = tmp_path / "21-files"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("ok", encoding="utf-8")
    (root / "assets" / "a.txt").write_text("a", encoding="utf-8")
    sftp = FakeSftp()
    publisher = SftpTargetPublisher(lambda: FakeClient(sftp))
    result = publisher.publish(PublishArtifact(root, "index.html", "file", True), make_target())
    assert result.publish_url == "https://internal.example/content/21-files/"
    assert {remote for _, remote in sftp.uploads} == {
        "/srv/content/21-files/index.html", "/srv/content/21-files/assets/a.txt",
    }


def test_sftp_authentication_failure_is_sanitized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD", "super-secret")
    publisher = SftpTargetPublisher(lambda: FakeClient(FakeSftp(), paramiko.AuthenticationException("super-secret")))
    with pytest.raises(PublishAuthenticationError, match="SFTP 认证失败") as exc:
        publisher.test_connection(make_target())
    assert "super-secret" not in str(exc.value)
