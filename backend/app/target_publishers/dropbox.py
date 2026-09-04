import json
from pathlib import Path
from urllib.parse import quote

import httpx

from app.core.constants import ContentType
from app.core.exceptions import PublishTargetConfigurationError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.services.artifact_packaging_service import ArtifactPackagingService
from app.services.credential_service import CredentialService
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.target_publishers.http import RemoteHttpPublisher


class DropboxTargetPublisher(BaseTargetPublisher, RemoteHttpPublisher):
    capability = TargetCapability(supports_directory=False, supports_file=True, supports_web_entry=False)
    api_root = "https://api.dropboxapi.com/2"
    content_root = "https://content.dropboxapi.com/2"
    simple_upload_limit = 150 * 1024 * 1024
    upload_chunk_size = 8 * 1024 * 1024

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        RemoteHttpPublisher.__init__(self, transport)

    def validate_target(self, target: PublishTarget) -> None:
        self.require_config(target, "folder_path")
        if not target.credential_ref:
            raise PublishTargetConfigurationError("Dropbox 发布目标缺少 credential_ref")

    @staticmethod
    def _reject_dynamic(artifact: PublishArtifact) -> None:
        if artifact.content_type == ContentType.DYNAMIC.value:
            raise PublishTargetConfigurationError("动态页面不能作为 Dropbox Web Hosting 内容发布")

    @staticmethod
    def _remote_path(artifact: PublishArtifact, target: PublishTarget, source: Path) -> str:
        folder = str((target.config or {})["folder_path"]).replace("\\", "/").strip("/")
        name = f"{artifact.generated_path}.zip" if artifact.is_directory else f"{artifact.generated_path}-{source.name}"
        return f"/{'/'.join(part for part in (folder, name) if part)}"

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _upload_large(
        self, client: httpx.Client, source: Path, remote_path: str, token: str,
    ) -> dict[str, object]:
        total = source.stat().st_size
        with source.open("rb") as stream:
            first = stream.read(self.upload_chunk_size)
            start = self.request(
                client, "POST", f"{self.content_root}/files/upload_session/start",
                headers={**self._auth(token), "Content-Type": "application/octet-stream", "Dropbox-API-Arg": json.dumps({"close": False})},
                content=first, operation="Dropbox 创建上传会话",
            ).json()
            session_id = start.get("session_id")
            if not session_id:
                raise PublishUploadError("Dropbox 上传会话响应无效")
            offset = len(first)
            while total - offset > self.upload_chunk_size:
                chunk = stream.read(self.upload_chunk_size)
                self.request(
                    client, "POST", f"{self.content_root}/files/upload_session/append_v2",
                    headers={
                        **self._auth(token), "Content-Type": "application/octet-stream",
                        "Dropbox-API-Arg": json.dumps({"cursor": {"session_id": session_id, "offset": offset}, "close": False}),
                    },
                    content=chunk, operation="Dropbox 分片上传",
                )
                offset += len(chunk)
            final_chunk = stream.read()
            return self.request(
                client, "POST", f"{self.content_root}/files/upload_session/finish",
                headers={
                    **self._auth(token), "Content-Type": "application/octet-stream",
                    "Dropbox-API-Arg": json.dumps({
                        "cursor": {"session_id": session_id, "offset": offset},
                        "commit": {"path": remote_path, "mode": "overwrite", "autorename": False, "mute": True},
                    }),
                },
                content=final_chunk, operation="Dropbox 完成上传",
            ).json()

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        self._reject_dynamic(artifact)
        source = ArtifactPackagingService.package_directory(artifact)
        remote_path = self._remote_path(artifact, target, source)
        token = CredentialService.get_secret(target.credential_ref, "token")
        with self.client() as client:
            if source.stat().st_size <= self.simple_upload_limit:
                with source.open("rb") as stream:
                    result = self.request(
                        client, "POST", f"{self.content_root}/files/upload",
                        headers={
                            **self._auth(token), "Content-Type": "application/octet-stream",
                            "Dropbox-API-Arg": json.dumps({"path": remote_path, "mode": "overwrite", "autorename": False, "mute": True}),
                        },
                        content=stream, operation="Dropbox 上传文件",
                    ).json()
            else:
                result = self._upload_large(client, source, remote_path, token)
        parent, _, name = remote_path.rpartition("/")
        web_url = f"https://www.dropbox.com/home{quote(parent or '/', safe='/')}?preview={quote(name, safe='')}"
        return TargetPublishResult(
            True, web_url, remote_path, "Dropbox 文件发布成功", str(result.get("id") or "") or None,
        )

    def test_connection(self, target: PublishTarget) -> bool:
        self.validate_target(target)
        token = CredentialService.get_secret(target.credential_ref, "token")
        with self.client() as client:
            self.request(
                client, "POST", f"{self.api_root}/users/get_current_account",
                headers={**self._auth(token), "Content-Type": "application/json"},
                json=None, operation="Dropbox 检查账号",
            )
        return True
