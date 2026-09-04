from pathlib import Path

import pytest

from app.core.exceptions import PublishTargetConfigurationError
from app.services.credential_service import CredentialService


def test_reads_publish_credential_from_backend_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("PUBLISH_CREDENTIAL_PUBLISH_TEST_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setattr(CredentialService, "credential_env_file", env_file)
    monkeypatch.delenv("PUBLISH_CREDENTIAL_PUBLISH_TEST_TOKEN", raising=False)

    assert CredentialService.get_secret("publish_test", "token") == "file-token"


def test_process_environment_takes_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("PUBLISH_CREDENTIAL_PUBLISH_TEST_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setattr(CredentialService, "credential_env_file", env_file)
    monkeypatch.setenv("PUBLISH_CREDENTIAL_PUBLISH_TEST_TOKEN", "process-token")

    assert CredentialService.get_secret("publish-test", "token") == "process-token"


def test_missing_publish_credential_remains_sanitized(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(CredentialService, "credential_env_file", tmp_path / "missing.env")
    monkeypatch.delenv("PUBLISH_CREDENTIAL_MISSING_TOKEN", raising=False)

    with pytest.raises(PublishTargetConfigurationError, match="missing/token"):
        CredentialService.get_secret("missing", "token")
