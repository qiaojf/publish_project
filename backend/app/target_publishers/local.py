import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from app.core.config import get_settings
from app.core.exceptions import PublishPermissionError, PublishTargetConfigurationError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.utils.paths import build_view_url, resolve_publish_root, safe_child


class LocalTargetPublisher(BaseTargetPublisher):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=True)

    def validate_target(self, target: PublishTarget) -> None:
        if not target.publish_root or not target.base_url:
            raise PublishTargetConfigurationError("Local 发布目标缺少 publish_root 或 base_url")
        configured = urlsplit(get_settings().local_published_base_url.rstrip("/"))
        target_url = urlsplit(target.base_url.rstrip("/"))
        configured_path = configured.path.rstrip("/")
        target_path = target_url.path.rstrip("/")
        if (
            target_url.scheme.lower() == configured.scheme.lower()
            and target_url.netloc.lower() == configured.netloc.lower()
            and (target_path == configured_path or target_path.startswith(f"{configured_path}/"))
        ):
            relative_url_path = target_path[len(configured_path):].strip("/")
            expected_root = safe_child(
                get_settings().local_published_root,
                *([part for part in relative_url_path.split("/") if part]),
            )
            actual_root = resolve_publish_root(target.publish_root)
            if actual_root != expected_root:
                raise PublishTargetConfigurationError(
                    f"Local 发布根目录与 URL 根地址不匹配；当前 URL 应对应目录：{expected_root}"
                )

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        assert target.publish_root and target.base_url
        publish_root = resolve_publish_root(target.publish_root)
        destination = safe_child(publish_root, artifact.generated_path)
        try:
            publish_root.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if destination.is_dir():
                    shutil.rmtree(destination)
                else:
                    destination.unlink()
            if artifact.is_directory:
                shutil.copytree(artifact.local_path, destination)
                publish_url = build_view_url(target.base_url, artifact.generated_path)
            else:
                destination.mkdir(parents=True, exist_ok=True)
                output = safe_child(destination, artifact.local_path.name)
                shutil.copy2(artifact.local_path, output)
                publish_url = f"{build_view_url(target.base_url, artifact.generated_path)}{artifact.local_path.name}"
        except PermissionError as exc:
            raise PublishPermissionError("Local 发布目录没有写入权限") from exc
        except OSError as exc:
            raise PublishUploadError("Local 发布文件写入失败") from exc
        return TargetPublishResult(True, publish_url, str(destination), "本地目录发布成功")

    def test_connection(self, target: PublishTarget) -> bool:
        self.validate_target(target)
        assert target.publish_root
        root = resolve_publish_root(target.publish_root)
        try:
            root.mkdir(parents=True, exist_ok=True)
            return root.is_dir() and os.access(root, os.W_OK)
        except PermissionError as exc:
            raise PublishPermissionError("Local 发布目录没有写入权限") from exc
        except OSError as exc:
            raise PublishUploadError("Local 发布目录不可用") from exc
