import os
import re
from pathlib import Path

from dotenv import dotenv_values

from app.core.config import BACKEND_ROOT
from app.core.exceptions import PublishTargetConfigurationError


class CredentialService:
    credential_env_file: Path = BACKEND_ROOT / ".env"

    @staticmethod
    def environment_name(credential_ref: str, key: str) -> str:
        ref = re.sub(r"[^A-Za-z0-9]+", "_", credential_ref).strip("_").upper()
        secret_key = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_").upper()
        return f"PUBLISH_CREDENTIAL_{ref}_{secret_key}"

    @classmethod
    def _read_value(cls, credential_ref: str, key: str) -> str | None:
        environment_name = cls.environment_name(credential_ref, key)
        process_value = os.getenv(environment_name)
        if process_value:
            return process_value

        file_value = dotenv_values(cls.credential_env_file).get(environment_name)
        return str(file_value) if file_value else None

    @classmethod
    def get_secret(cls, credential_ref: str | None, key: str) -> str:
        if not credential_ref:
            raise PublishTargetConfigurationError("发布目标未配置 credential_ref")
        value = cls._read_value(credential_ref, key)
        if not value:
            raise PublishTargetConfigurationError(f"发布目标凭证未配置：{credential_ref}/{key}")
        return value

    @classmethod
    def get_optional_secret(cls, credential_ref: str | None, key: str) -> str | None:
        if not credential_ref:
            return None
        return cls._read_value(credential_ref, key)
