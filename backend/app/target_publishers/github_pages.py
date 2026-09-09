import time
from urllib.parse import quote

from app.core.config import get_settings
from app.core.constants import ContentType
from app.core.exceptions import PublishTargetConfigurationError, PublishTimeoutError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.target_publishers.base import PublishArtifact, TargetCapability, TargetPublishResult
from app.target_publishers.github import GitHubTargetPublisher


class GitHubPagesTargetPublisher(GitHubTargetPublisher):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=True)
    deployment_poll_interval_seconds = 2.0

    def validate_target(self, target) -> None:
        super().validate_target(target)
        self.require_config(target, "base_url")

    def validate_artifact(self, artifact: PublishArtifact) -> None:
        if artifact.content_type == ContentType.DYNAMIC.value:
            raise PublishTargetConfigurationError("动态页面依赖后端运行，不能发布到 GitHub Pages")
        if artifact.is_directory and not artifact.entry_file:
            raise PublishTargetConfigurationError("GitHub Pages Artifact 缺少 Web 入口文件")
        oversized = next(((relative, local_file.stat().st_size) for local_file, relative in self.artifact_files(artifact) if local_file.stat().st_size > self.regular_blob_limit_bytes), None)
        if oversized:
            relative, size = oversized
            raise PublishTargetConfigurationError(
                f"文件 {relative} 大小为 {size / 1024 / 1024:.1f} MiB，超过 GitHub 普通 Git 文件 100 MiB 限制；"
                "GitHub Pages 官方不支持 Git LFS，请改用公司服务器、SFTP、OneDrive 或 Dropbox 目标"
            )

    @staticmethod
    def _prefix(config: dict[str, object], artifact: PublishArtifact) -> str:
        repo_path = str(config.get("repo_path") or "").replace("\\", "/").strip("/")
        if not artifact.is_directory:
            return repo_path
        return "/".join(part for part in (repo_path, artifact.generated_path) if part)

    def _files_for_publish(self, artifact: PublishArtifact):
        return self.artifact_files(artifact)

    def _delete_stale_files(self, artifact: PublishArtifact) -> bool:
        return artifact.is_directory

    def _publish_url(
        self, config: dict[str, object], prefix: str, published_paths: tuple[str, ...], artifact: PublishArtifact,
    ) -> str:
        if not artifact.is_directory:
            encoded_file = quote(published_paths[0].strip("/"), safe="/")
            return f"{str(config['base_url']).rstrip('/')}/{encoded_file}"
        encoded_path = quote(prefix.strip("/"), safe="/")
        return f"{str(config['base_url']).rstrip('/')}/{encoded_path}/"

    def _pages_configuration(self, target: PublishTarget) -> dict[str, object]:
        config = target.config or {}
        token = self._headers_token(target)
        with self.client() as client:
            pages = self.request(
                client, "GET", f"{self._repo_api(config)}/pages", headers=self._headers(token),
                operation="GitHub Pages 检查配置",
            ).json()
        if pages.get("build_type") == "legacy":
            source = pages.get("source") or {}
            source_branch = str(source.get("branch") or "")
            configured_branch = str(config.get("branch") or "")
            if source_branch != configured_branch:
                raise PublishTargetConfigurationError(
                    f"GitHub Pages 发布分支为 {source_branch or '未设置'}，当前目标配置为 {configured_branch or '未设置'}"
                )
        configured_url = str(config.get("base_url") or "").rstrip("/")
        pages_url = str(pages.get("html_url") or "").rstrip("/")
        if pages_url and configured_url != pages_url:
            raise PublishTargetConfigurationError(
                f"GitHub Pages 地址应配置为 {pages_url}/"
            )
        return pages

    @staticmethod
    def _headers_token(target: PublishTarget) -> str:
        from app.services.credential_service import CredentialService

        return CredentialService.get_secret(target.credential_ref, "token")

    def _wait_for_deployment(self, target: PublishTarget, commit_sha: str) -> None:
        config = target.config or {}
        token = self._headers_token(target)
        headers = self._headers(token)
        latest_build_url = f"{self._repo_api(config)}/pages/builds/latest"
        deadline = time.monotonic() + get_settings().publish_operation_timeout_seconds
        with self.client() as client:
            while True:
                build = self.request(
                    client, "GET", latest_build_url, headers=headers,
                    operation="GitHub Pages 检查部署状态",
                ).json()
                if str(build.get("commit") or "") == commit_sha:
                    status = str(build.get("status") or "")
                    if status == "built":
                        return
                    if status in {"errored", "canceled"}:
                        raise PublishUploadError("GitHub Pages 部署失败")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise PublishTimeoutError("GitHub Pages 部署等待超时")
                time.sleep(min(self.deployment_poll_interval_seconds, remaining))

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        self.validate_artifact(artifact)
        self._pages_configuration(target)
        result = super().publish(artifact, target)
        if not result.external_id:
            raise PublishUploadError("GitHub Pages 提交结果缺少 commit")
        self._wait_for_deployment(target, result.external_id)
        return TargetPublishResult(
            success=result.success,
            publish_url=result.publish_url,
            remote_path=result.remote_path,
            message="GitHub Pages 部署成功",
            external_id=result.external_id,
        )

    def test_connection(self, target: PublishTarget) -> bool:
        super().test_connection(target)
        self._pages_configuration(target)
        return True
