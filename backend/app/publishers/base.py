from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.db.models.content import Content
from app.db.models.publish_target import PublishTarget
from app.utils.paths import build_view_url, resolve_publish_root, safe_child
from app.utils.slug import safe_slug


@dataclass(frozen=True)
class PublishResult:
    relative_path: str
    output_path: str
    view_url: str


class BasePublisher(ABC):
    @abstractmethod
    def publish(self, content: Content, target: PublishTarget) -> PublishResult:
        raise NotImplementedError

    @staticmethod
    def prepare_output(content: Content, target: PublishTarget) -> tuple[str, Path, str]:
        relative_path = f"{content.id}-{safe_slug(content.title)}"
        publish_root = resolve_publish_root(target.publish_root)
        output_dir = safe_child(publish_root, relative_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        return relative_path, output_dir, build_view_url(target.base_url, relative_path)
