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


class OneDriveTargetPublisher(BaseTargetPublisher, RemoteHttpPublisher):
    capability = TargetCapability(supports_directory=False, supports_file=True, supports_web_entry=False)
    graph_root = "https://graph.microsoft.com/v1.0"
    simple_upload_limit = 250 * 1024 * 1024
    upload_chunk_size = 10 * 1024 * 1024

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        RemoteHttpPublisher.__init__(self, transport)

    def validate_target(self, target: PublishTarget) -> None:
        self.require_config(target, "tenant_id", "client_id", "drive_id", "folder_path")
        if not target.credential_ref:
            raise PublishTargetConfigurationError("OneDrive 发布目标缺少 credential_ref")

    @staticmethod
    def _reject_dynamic(artifact: PublishArtifact) -> None:
        if artifact.content_type == ContentType.DYNAMIC.value:
            raise PublishTargetConfigurationError("动态页面不能作为 OneDrive Web Hosting 内容发布")

    def _access_token(self, client: httpx.Client, target: PublishTarget) -> str:
        config = target.config or {}
        secret = CredentialService.get_secret(target.credential_ref, "client_secret")
        response = self.request(
            client, "POST",
            f"https://login.microsoftonline.com/{quote(str(config['tenant_id']), safe='')}/oauth2/v2.0/token",
            data={
                "client_id": str(config["client_id"]),
                "scope": "https://graph.microsoft.com/.default",
                "client_secret": secret,
                "grant_type": "client_credentials",
            },
            operation="OneDrive 获取访问令牌",
        )
        token = response.json().get("access_token")
        if not token:
            raise PublishUploadError("OneDrive 访问令牌响应无效")
        return str(token)

    @staticmethod
    def _remote_path(artifact: PublishArtifact, target: PublishTarget, source: Path) -> str:
        folder = str((target.config or {})["folder_path"]).replace("\\", "/").strip("/")
        file_name = f"{artifact.generated_path}.zip" if artifact.is_directory else source.name
        return "/".join(part for part in (folder, file_name) if part)

    def _upload_large(
        self, client: httpx.Client, endpoint: str, source: Path, headers: dict[str, str],
    ) -> dict[str, object]:
        session = self.request(
            client, "POST", f"{endpoint}:/createUploadSession", headers=headers,
            json={"item": {"@microsoft.graph.conflictBehavior": "replace", "name": source.name}},
            operation="OneDrive 创建上传会话",
        ).json()
        upload_url = session.get("uploadUrl")
        if not upload_url:
            raise PublishUploadError("OneDrive 上传会话响应无效")
        total = source.stat().st_size
        final: dict[str, object] = {}
        with source.open("rb") as stream:
            offset = 0
            while offset < total:
                chunk = stream.read(self.upload_chunk_size)
                end = offset + len(chunk) - 1
                response = self.request(
                    client, "PUT", str(upload_url), content=chunk,
                    headers={"Content-Length": str(len(chunk)), "Content-Range": f"bytes {offset}-{end}/{total}"},
                    expected=(200, 201, 202), operation="OneDrive 分片上传",
                )
                if response.status_code in {200, 201}:
                    final = response.json()
                offset = end + 1
        return final

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        self._reject_dynamic(artifact)
        source = ArtifactPackagingService.package_directory(artifact)
        remote_path = self._remote_path(artifact, target, source)
        config = target.config or {}
        drive_id = quote(str(config["drive_id"]), safe="")
        encoded_path = quote(remote_path, safe="/")
        endpoint = f"{self.graph_root}/drives/{drive_id}/root:/{encoded_path}"
        with self.client() as client:
            token = self._access_token(client, target)
            headers = {"Authorization": f"Bearer {token}"}
            if source.stat().st_size <= self.simple_upload_limit:
                with source.open("rb") as stream:
                    result = self.request(
                        client, "PUT", f"{endpoint}:/content", headers=headers,
                        content=stream, expected=(200, 201), operation="OneDrive 上传文件",
                    ).json()
            else:
                result = self._upload_large(client, endpoint, source, headers)
        web_url = result.get("webUrl")
        if not web_url:
            raise PublishUploadError("OneDrive 上传成功但未返回 Web URL")
        return TargetPublishResult(
            True, str(web_url), f"/{remote_path}", "OneDrive 文件发布成功", str(result.get("id") or "") or None,
        )

    def test_connection(self, target: PublishTarget) -> bool:
        self.validate_target(target)
        config = target.config or {}
        drive_id = quote(str(config["drive_id"]), safe="")
        with self.client() as client:
            token = self._access_token(client, target)
            self.request(
                client, "GET", f"{self.graph_root}/drives/{drive_id}",
                headers={"Authorization": f"Bearer {token}"}, operation="OneDrive 检查 Drive",
            )
        return True
