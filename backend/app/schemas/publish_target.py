from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import ContentType, PUBLISH_TARGET_CONTENT_TYPES, PublishTargetType


TARGET_CONFIG_FIELDS: dict[PublishTargetType, tuple[str, ...]] = {
    PublishTargetType.LOCAL: (),
    PublishTargetType.SFTP: ("host", "port", "username", "remote_root", "base_url"),
    PublishTargetType.GITHUB: ("owner", "repo", "branch", "repo_path"),
    PublishTargetType.GITHUB_PAGES: ("owner", "repo", "branch", "repo_path", "base_url"),
    PublishTargetType.ONEDRIVE: ("tenant_id", "client_id", "drive_id", "folder_path"),
    PublishTargetType.DROPBOX: ("folder_path",),
}

SECRET_FIELD_MARKERS = ("token", "password", "secret", "private_key", "passphrase")


def _contains_secret(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(marker in normalized for marker in SECRET_FIELD_MARKERS) or _contains_secret(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return False


class PublishTargetPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_type: PublishTargetType = PublishTargetType.LOCAL
    content_types: list[ContentType] = Field(min_length=1)
    publish_root: str | None = Field(default=None, max_length=1000)
    base_url: str | None = Field(default=None, max_length=1000)
    config: dict[str, Any] = Field(default_factory=dict)
    credential_ref: str | None = Field(default=None, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    enabled: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("publish_root", "base_url", "credential_ref")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        stripped = value.strip() if value else None
        return stripped or None

    @field_validator("content_types")
    @classmethod
    def unique_types(cls, value: list[ContentType]) -> list[ContentType]:
        return list(dict.fromkeys(value))

    @field_validator("config")
    @classmethod
    def reject_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        if _contains_secret(value):
            raise ValueError("敏感凭证不能保存在 config，请使用 credential_ref 引用环境变量")
        return value

    @model_validator(mode="after")
    def validate_target_configuration(self) -> "PublishTargetPayload":
        unsupported = [item.value for item in self.content_types if item not in PUBLISH_TARGET_CONTENT_TYPES[self.target_type]]
        if unsupported:
            if self.target_type == PublishTargetType.GITHUB_PAGES:
                raise ValueError("GitHub Pages 仅支持静态内容，不支持动态页面")
            raise ValueError(f"{self.target_type.value} 不支持内容类型：{', '.join(unsupported)}")
        if self.target_type == PublishTargetType.LOCAL:
            if not self.publish_root:
                raise ValueError("Local 发布目标必须配置 publish_root")
            if not self.base_url or not (
                self.base_url.startswith(("http://", "https://"))
                or (self.base_url.startswith("/") and not self.base_url.startswith("//"))
            ):
                raise ValueError("Local 发布目标必须配置有效的 HTTP(S) 或站点相对 base_url")
            self.config = {}
            self.credential_ref = None
            return self

        missing = [field for field in TARGET_CONFIG_FIELDS[self.target_type] if self.config.get(field) in (None, "")]
        if missing:
            raise ValueError(f"{self.target_type.value} 缺少配置字段：{', '.join(missing)}")
        if not self.credential_ref:
            raise ValueError(f"{self.target_type.value} 发布目标必须配置 credential_ref")
        if self.target_type == PublishTargetType.SFTP:
            try:
                port = int(self.config.get("port", 22))
            except (TypeError, ValueError) as exc:
                raise ValueError("SFTP port 必须是有效端口") from exc
            if not 1 <= port <= 65535:
                raise ValueError("SFTP port 必须在 1 到 65535 之间")
            self.config["port"] = port
        base_url = self.config.get("base_url")
        if base_url and not str(base_url).startswith(("http://", "https://")):
            raise ValueError("base_url 必须是有效的 HTTP(S) URL")
        self.publish_root = None
        self.base_url = None
        return self


class PublishTargetStatusUpdate(BaseModel):
    enabled: bool


class PublishTargetEmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_type: PublishTargetType
    content_types: list[ContentType]
    enabled: bool


class PublishTargetAdminRead(PublishTargetEmployeeRead):
    publish_root: str | None = None
    base_url: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    credential_ref: str | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime


class PublishTargetConnectionRead(BaseModel):
    connected: bool
