import shutil
import time
from pathlib import Path
from uuid import uuid4

import httpx

from app.core.config import get_settings
from app.core.exceptions import PublishError, PublishTargetConfigurationError, PublishTimeoutError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.services.credential_service import CredentialService
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.target_publishers.http import RemoteHttpPublisher
from app.utils.paths import build_file_url, safe_child


class InstagramTargetPublisher(BaseTargetPublisher, RemoteHttpPublisher):
    capability = TargetCapability(supports_directory=False, supports_file=True, supports_web_entry=False)
    graph_root = "https://graph.instagram.com"
    status_poll_interval_seconds = 2.0
    max_video_size_bytes = 1024 * 1024 * 1024
    supported_extensions = {".mp4", ".mov"}

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        RemoteHttpPublisher.__init__(self, transport)

    def validate_target(self, target: PublishTarget) -> None:
        config = self.require_config(target, "ig_user_id", "api_version", "media_base_url")
        if not str(config["ig_user_id"]).strip().isdigit():
            raise PublishTargetConfigurationError("Instagram ig_user_id 必须是纯数字账号 ID")
        version = str(config["api_version"]).strip()
        if not version.startswith("v") or not version[1:].replace(".", "", 1).isdigit():
            raise PublishTargetConfigurationError("Instagram api_version 格式应类似 v23.0")
        if not str(config["media_base_url"]).strip().startswith("https://"):
            raise PublishTargetConfigurationError("Instagram media_base_url 必须是公网 HTTPS URL")
        if not target.credential_ref:
            raise PublishTargetConfigurationError(
                "Instagram 发布目标缺少 credential_ref", "PUBLISH_TARGET_CREDENTIAL_MISSING"
            )

    def validate_artifact(self, artifact: PublishArtifact) -> None:
        if artifact.is_directory or not artifact.local_path.is_file():
            raise PublishTargetConfigurationError("Instagram 只能发布单个视频文件")
        if artifact.local_path.suffix.lower() not in self.supported_extensions:
            raise PublishTargetConfigurationError("Instagram 视频仅支持 MP4 或 MOV 文件")
        if artifact.local_path.stat().st_size > self.max_video_size_bytes:
            raise PublishTargetConfigurationError("Instagram 视频不能超过 1 GB")

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _caption(artifact: PublishArtifact) -> str | None:
        parts = [part.strip() for part in (artifact.title, artifact.description) if part and part.strip()]
        caption = "\n\n".join(parts)
        return caption[:2200] or None

    @staticmethod
    def _stage_video(artifact: PublishArtifact, media_base_url: str) -> tuple[Path, str]:
        staging_root = safe_child(get_settings().local_published_root, "_instagram")
        staging_root.mkdir(parents=True, exist_ok=True)
        staging_directory = safe_child(staging_root, uuid4().hex)
        staging_directory.mkdir(parents=True, exist_ok=False)
        destination = safe_child(staging_directory, artifact.local_path.name)
        shutil.copy2(artifact.local_path, destination)
        return destination, build_file_url(media_base_url, f"{staging_directory.name}/{destination.name}")

    def _wait_until_ready(
        self, client: httpx.Client, api_version: str, container_id: str, headers: dict[str, str],
    ) -> None:
        deadline = time.monotonic() + get_settings().publish_operation_timeout_seconds
        endpoint = f"{self.graph_root}/{api_version}/{container_id}"
        while True:
            status_data = self.request(
                client,
                "GET",
                endpoint,
                headers=headers,
                params={"fields": "status_code,status"},
                operation="Instagram 检查视频处理状态",
            ).json()
            status_code = str(status_data.get("status_code") or "").upper()
            if status_code == "FINISHED":
                return
            if status_code in {"ERROR", "EXPIRED"}:
                raise PublishUploadError(f"Instagram 视频处理失败：{status_code}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PublishTimeoutError("Instagram 视频处理等待超时")
            time.sleep(min(self.status_poll_interval_seconds, remaining))

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        self.validate_artifact(artifact)
        config = target.config or {}
        api_version = str(config["api_version"]).strip()
        ig_user_id = str(config["ig_user_id"]).strip()
        access_token = CredentialService.get_secret(target.credential_ref, "access_token")
        headers = self._headers(access_token)
        staged_file, video_url = self._stage_video(artifact, str(config["media_base_url"]))
        caption = self._caption(artifact)
        container_payload: dict[str, object] = {
            "media_type": "REELS",
            "video_url": video_url,
            "share_to_feed": "true",
        }
        if caption:
            container_payload["caption"] = caption

        try:
            with self.client() as client:
                container = self.request(
                    client,
                    "POST",
                    f"{self.graph_root}/{api_version}/{ig_user_id}/media",
                    headers=headers,
                    data=container_payload,
                    operation="Instagram 创建视频容器",
                ).json()
                container_id = str(container.get("id") or "")
                if not container_id:
                    raise PublishUploadError("Instagram 创建视频容器后未返回 ID")
                self._wait_until_ready(client, api_version, container_id, headers)
                published = self.request(
                    client,
                    "POST",
                    f"{self.graph_root}/{api_version}/{ig_user_id}/media_publish",
                    headers=headers,
                    data={"creation_id": container_id},
                    operation="Instagram 发布 Reels",
                ).json()
                media_id = str(published.get("id") or "")
                if not media_id:
                    raise PublishUploadError("Instagram 发布成功响应缺少媒体 ID")
                permalink = ""
                try:
                    media = self.request(
                        client,
                        "GET",
                        f"{self.graph_root}/{api_version}/{media_id}",
                        headers=headers,
                        params={"fields": "permalink"},
                        operation="Instagram 读取发布链接",
                    ).json()
                    permalink = str(media.get("permalink") or "")
                except (PublishError, ValueError):
                    permalink = ""
        finally:
            shutil.rmtree(staged_file.parent, ignore_errors=True)

        return TargetPublishResult(
            True,
            permalink or "https://www.instagram.com/",
            f"instagram:{media_id}",
            "Instagram Reels 发布成功",
            media_id,
        )

    def test_connection(self, target: PublishTarget) -> bool:
        self.validate_target(target)
        config = target.config or {}
        access_token = CredentialService.get_secret(target.credential_ref, "access_token")
        with self.client() as client:
            account = self.request(
                client,
                "GET",
                f"{self.graph_root}/{config['api_version']}/{config['ig_user_id']}",
                headers=self._headers(access_token),
                params={"fields": "id,username"},
                operation="Instagram 检查专业账号",
            ).json()
        if str(account.get("id") or "") != str(config["ig_user_id"]):
            raise PublishTargetConfigurationError("Instagram 返回账号与配置的 ig_user_id 不一致")
        return True
