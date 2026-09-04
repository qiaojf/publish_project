from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from app.core.exceptions import PublishTargetConfigurationError
from app.db.models.publish_target import PublishTarget


@dataclass(frozen=True)
class PublishArtifact:
    local_path: Path
    entry_file: str | None
    content_type: str
    is_directory: bool

    @property
    def generated_path(self) -> str:
        return self.local_path.name


@dataclass(frozen=True)
class TargetPublishResult:
    success: bool
    publish_url: str | None
    remote_path: str | None
    message: str | None = None
    external_id: str | None = None


@dataclass(frozen=True)
class TargetCapability:
    supports_directory: bool
    supports_file: bool
    supports_web_entry: bool


class BaseTargetPublisher(ABC):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=False)

    @abstractmethod
    def validate_target(self, target: PublishTarget) -> None:
        raise NotImplementedError

    @abstractmethod
    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        raise NotImplementedError

    @abstractmethod
    def test_connection(self, target: PublishTarget) -> bool:
        raise NotImplementedError

    @staticmethod
    def require_config(target: PublishTarget, *fields: str) -> dict[str, object]:
        config = target.config or {}
        missing = [field for field in fields if config.get(field) in (None, "")]
        if missing:
            raise PublishTargetConfigurationError(
                f"发布目标缺少配置字段：{', '.join(missing)}",
            )
        return config

    @staticmethod
    def artifact_files(artifact: PublishArtifact) -> Iterator[tuple[Path, str]]:
        if artifact.is_directory:
            for path in sorted(item for item in artifact.local_path.rglob("*") if item.is_file()):
                yield path, path.relative_to(artifact.local_path).as_posix()
        else:
            yield artifact.local_path, artifact.local_path.name
