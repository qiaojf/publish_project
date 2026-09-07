import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import httpx

from app.core.exceptions import PublishTargetConfigurationError, PublishTimeoutError, PublishUploadError
from app.db.models.publish_target import PublishTarget
from app.services.credential_service import CredentialService
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.target_publishers.http import RemoteHttpPublisher


class GitHubTargetPublisher(BaseTargetPublisher, RemoteHttpPublisher):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=False)
    api_root = "https://api.github.com"
    regular_blob_limit_bytes = 100 * 1024 * 1024
    lfs_media_type = "application/vnd.git-lfs+json"

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

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _lfs_pointer(oid: str, size: int) -> bytes:
        return f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n".encode()

    @staticmethod
    def _lfs_headers(token: str) -> dict[str, str]:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
        return {
            "Accept": GitHubTargetPublisher.lfs_media_type,
            "Content-Type": GitHubTargetPublisher.lfs_media_type,
            "Authorization": f"Basic {basic}",
        }

    def _upload_lfs_bytes(self, client: httpx.Client, local_file: Path, upload: dict[str, object], relative_path: str) -> None:
        href = str(upload.get("href") or "")
        if not href.startswith("https://"):
            raise PublishUploadError("GitHub LFS 返回了无效的上传地址")
        raw_headers = upload.get("header") or {}
        headers = {str(key): str(value) for key, value in raw_headers.items()} if isinstance(raw_headers, dict) else {}
        response: httpx.Response | None = None
        for attempt in range(3):
            try:
                with local_file.open("rb") as stream:
                    response = client.put(href, headers=headers, content=stream)
            except httpx.TimeoutException as exc:
                if attempt == 2:
                    raise PublishTimeoutError(f"GitHub LFS 上传大文件 {relative_path} 超时") from exc
                continue
            except httpx.HTTPError as exc:
                if attempt == 2:
                    raise PublishUploadError(f"GitHub LFS 上传大文件 {relative_path} 失败") from exc
                continue
            if response.status_code in {200, 201, 204}:
                return
            if response.status_code in self.retry_statuses and attempt < 2:
                continue
            break
        raise PublishUploadError(f"GitHub LFS 上传大文件 {relative_path} 失败（HTTP {response.status_code if response else 'unknown'}）")

    def _upload_lfs_object(self, client: httpx.Client, config: dict[str, object], token: str, local_file: Path, relative_path: str) -> bytes:
        size = local_file.stat().st_size
        oid = self._sha256(local_file)
        owner = quote(str(config["owner"]), safe="")
        repo = quote(str(config["repo"]), safe="")
        batch = self.request(
            client, "POST", f"https://github.com/{owner}/{repo}.git/info/lfs/objects/batch", headers=self._lfs_headers(token),
            json={"operation": "upload", "transfers": ["basic"], "ref": {"name": f"refs/heads/{config['branch']}"}, "objects": [{"oid": oid, "size": size}], "hash_algo": "sha256"},
            operation="GitHub LFS 申请上传",
        ).json()
        if not isinstance(batch, dict):
            raise PublishUploadError("GitHub LFS 响应格式不正确")
        objects = batch.get("objects") or []
        if not isinstance(objects, list):
            raise PublishUploadError("GitHub LFS 响应格式不正确")
        matched = next((item for item in objects if isinstance(item, dict) and str(item.get("oid") or "") == oid), None)
        if not isinstance(matched, dict):
            raise PublishUploadError("GitHub LFS 响应缺少上传对象")
        if matched.get("error"):
            error = matched["error"] if isinstance(matched["error"], dict) else {}
            raise PublishUploadError(f"GitHub LFS 拒绝文件 {relative_path}（HTTP {error.get('code', 'unknown')}）")
        actions = matched.get("actions") or {}
        if not isinstance(actions, dict):
            raise PublishUploadError("GitHub LFS 响应格式不正确")
        upload = actions.get("upload")
        if isinstance(upload, dict):
            self._upload_lfs_bytes(client, local_file, upload, relative_path)
        verify = actions.get("verify")
        if isinstance(verify, dict):
            verify_href = str(verify.get("href") or "")
            if not verify_href.startswith("https://"):
                raise PublishUploadError("GitHub LFS 返回了无效的校验地址")
            verify_headers = verify.get("header") or {}
            self.request(client, "POST", verify_href, headers={str(key): str(value) for key, value in verify_headers.items()} if isinstance(verify_headers, dict) else {}, json={"oid": oid, "size": size}, operation="GitHub LFS 校验上传")
        return self._lfs_pointer(oid, size)

    def _create_blob(self, client: httpx.Client, repo_api: str, headers: dict[str, str], content: bytes) -> str:
        encoded = base64.b64encode(content).decode("ascii")
        blob = self.request(client, "POST", f"{repo_api}/git/blobs", headers=headers, json={"content": encoded, "encoding": "base64"}, expected=(201,), operation="GitHub 上传文件").json()
        return str(blob["sha"])

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
            lfs_paths: list[str] = []
            for local_file, relative in local_files:
                remote_file = f"{prefix}/{relative}" if prefix else relative
                current_paths.add(remote_file)
                if local_file.stat().st_size > self.regular_blob_limit_bytes:
                    content = self._upload_lfs_object(client, config, token, local_file, relative); lfs_paths.append(relative)
                else:
                    content = local_file.read_bytes()
                tree_entries.append({"path": remote_file, "mode": "100644", "type": "blob", "sha": self._create_blob(client, repo_api, headers, content)})

            if lfs_paths:
                attributes_path = f"{prefix}/.gitattributes" if prefix else ".gitattributes"
                existing_attributes = next((path for path, relative in local_files if relative == ".gitattributes"), None)
                attributes = existing_attributes.read_bytes() if existing_attributes else b""
                if attributes and not attributes.endswith(b"\n"):
                    attributes += b"\n"
                attributes += "".join(f"{json.dumps(path, ensure_ascii=False)} filter=lfs diff=lfs merge=lfs -text\n" for path in lfs_paths).encode()
                current_paths.add(attributes_path)
                tree_entries = [entry for entry in tree_entries if entry["path"] != attributes_path]
                tree_entries.append({"path": attributes_path, "mode": "100644", "type": "blob", "sha": self._create_blob(client, repo_api, headers, attributes)})

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
