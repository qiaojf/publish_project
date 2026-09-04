import base64
from pathlib import PurePosixPath
from urllib.parse import quote

import httpx

from app.core.exceptions import PublishTargetConfigurationError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.services.credential_service import CredentialService
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.target_publishers.http import RemoteHttpPublisher


class GitHubTargetPublisher(BaseTargetPublisher, RemoteHttpPublisher):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=False)
    api_root = "https://api.github.com"

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        RemoteHttpPublisher.__init__(self, transport)

    def validate_target(self, target: PublishTarget) -> None:
        config = self.require_config(target, "owner", "repo", "branch", "repo_path")
        repo_path = str(config["repo_path"]).replace("\\", "/").strip("/")
        if ".." in PurePosixPath(repo_path).parts:
            raise PublishTargetConfigurationError("GitHub repo_path 不安全")
        if not target.credential_ref:
            raise PublishTargetConfigurationError("GitHub 发布目标缺少 credential_ref")

    def validate_artifact(self, artifact: PublishArtifact) -> None:
        return None

    @staticmethod
    def _headers(token: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    @staticmethod
    def _prefix(config: dict[str, object], artifact: PublishArtifact) -> str:
        repo_path = str(config.get("repo_path") or "").replace("\\", "/").strip("/")
        return "/".join(part for part in (repo_path, artifact.generated_path) if part)

    def _repo_api(self, config: dict[str, object]) -> str:
        owner = quote(str(config["owner"]), safe="")
        repo = quote(str(config["repo"]), safe="")
        return f"{self.api_root}/repos/{owner}/{repo}"

    def _publish_url(self, config: dict[str, object], prefix: str) -> str:
        owner = quote(str(config["owner"]), safe="")
        repo = quote(str(config["repo"]), safe="")
        branch = quote(str(config["branch"]), safe="")
        path = quote(prefix, safe="/")
        return f"https://github.com/{owner}/{repo}/tree/{branch}/{path}"

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        self.validate_target(target)
        self.validate_artifact(artifact)
        config = target.config or {}
        token = CredentialService.get_secret(target.credential_ref, "token")
        headers = self._headers(token)
        repo_api = self._repo_api(config)
        branch = quote(str(config["branch"]), safe="")
        prefix = self._prefix(config, artifact)
        local_files = list(self.artifact_files(artifact))
        if not local_files:
            raise PublishUploadError("GitHub 发布 Artifact 为空")

        with self.client() as client:
            ref = self.request(
                client, "GET", f"{repo_api}/git/ref/heads/{branch}", headers=headers,
                operation="GitHub 读取分支",
            ).json()
            head_sha = str(ref["object"]["sha"])
            commit = self.request(
                client, "GET", f"{repo_api}/git/commits/{quote(head_sha, safe='')}", headers=headers,
                operation="GitHub 读取提交",
            ).json()
            base_tree = str(commit["tree"]["sha"])
            existing_tree = self.request(
                client, "GET", f"{repo_api}/git/trees/{quote(base_tree, safe='')}",
                headers=headers, params={"recursive": "1"}, operation="GitHub 读取目录",
            ).json()

            tree_entries: list[dict[str, object]] = []
            current_paths: set[str] = set()
            for local_file, relative in local_files:
                remote_file = f"{prefix}/{relative}" if prefix else relative
                current_paths.add(remote_file)
                encoded = base64.b64encode(local_file.read_bytes()).decode("ascii")
                blob = self.request(
                    client, "POST", f"{repo_api}/git/blobs", headers=headers,
                    json={"content": encoded, "encoding": "base64"}, expected=(201,),
                    operation="GitHub 上传文件",
                ).json()
                tree_entries.append({"path": remote_file, "mode": "100644", "type": "blob", "sha": blob["sha"]})

            existing_prefix = f"{prefix}/" if prefix else ""
            for item in existing_tree.get("tree", []):
                existing_path = str(item.get("path") or "")
                if item.get("type") == "blob" and existing_path.startswith(existing_prefix) and existing_path not in current_paths:
                    tree_entries.append({"path": existing_path, "mode": "100644", "type": "blob", "sha": None})

            tree = self.request(
                client, "POST", f"{repo_api}/git/trees", headers=headers,
                json={"base_tree": base_tree, "tree": tree_entries}, expected=(201,),
                operation="GitHub 创建目录树",
            ).json()
            new_commit = self.request(
                client, "POST", f"{repo_api}/git/commits", headers=headers,
                json={"message": f"Publish content {artifact.generated_path}", "tree": tree["sha"], "parents": [head_sha]},
                expected=(201,), operation="GitHub 创建提交",
            ).json()
            commit_sha = str(new_commit["sha"])
            self.request(
                client, "PATCH", f"{repo_api}/git/refs/heads/{branch}", headers=headers,
                json={"sha": commit_sha, "force": False}, operation="GitHub 更新分支",
            )
        return TargetPublishResult(
            True, self._publish_url(config, prefix), f"{config['owner']}/{config['repo']}:{config['branch']}/{prefix}",
            "GitHub Repository 提交成功", commit_sha,
        )

    def test_connection(self, target: PublishTarget) -> bool:
        self.validate_target(target)
        config = target.config or {}
        token = CredentialService.get_secret(target.credential_ref, "token")
        headers = self._headers(token)
        repo_api = self._repo_api(config)
        branch = quote(str(config["branch"]), safe="")
        with self.client() as client:
            repository = self.request(client, "GET", repo_api, headers=headers, operation="GitHub 检查仓库").json()
            permissions = repository.get("permissions") or {}
            if permissions and not permissions.get("push", False):
                from app.core.exceptions import PublishPermissionError
                raise PublishPermissionError("GitHub Token 没有仓库写入权限")
            self.request(
                client, "GET", f"{repo_api}/git/ref/heads/{branch}", headers=headers,
                operation="GitHub 检查分支",
            )
        return True
