import io
import posixpath
import socket
from pathlib import PurePosixPath
from typing import Any, Callable

from app.core.config import get_settings
from app.core.exceptions import (
    PublishAuthenticationError,
    PublishError,
    PublishPermissionError,
    PublishTargetConfigurationError,
    PublishTargetConnectionError,
    PublishTimeoutError,
    PublishUploadError,
)
from app.db.models.publish_target import PublishTarget
from app.services.credential_service import CredentialService
from app.target_publishers.base import BaseTargetPublisher, PublishArtifact, TargetCapability, TargetPublishResult
from app.utils.paths import build_file_url, build_view_url


class SftpTargetPublisher(BaseTargetPublisher):
    capability = TargetCapability(supports_directory=True, supports_file=True, supports_web_entry=True)

    def __init__(self, client_factory: Callable[[], Any] | None = None) -> None:
        self.client_factory = client_factory

    def validate_target(self, target: PublishTarget) -> None:
        config = self.require_config(target, "host", "port", "username", "remote_root", "base_url")
        remote_root = str(config["remote_root"])
        if not remote_root.startswith("/") or ".." in PurePosixPath(remote_root).parts:
            raise PublishTargetConfigurationError("SFTP remote_root 必须是安全的绝对路径")
        if not target.credential_ref:
            raise PublishTargetConfigurationError("SFTP 发布目标缺少 credential_ref")

    @staticmethod
    def _paramiko() -> Any:
        try:
            import paramiko
        except ImportError as exc:
            raise PublishTargetConfigurationError("SFTP 运行依赖 paramiko，当前环境尚未安装") from exc
        return paramiko

    def _private_key(self, module: Any, value: str, passphrase: str | None) -> Any:
        for key_class_name in ("Ed25519Key", "ECDSAKey", "RSAKey"):
            key_class = getattr(module, key_class_name, None)
            if key_class:
                try:
                    return key_class.from_private_key(io.StringIO(value), password=passphrase)
                except Exception:
                    continue
        raise PublishAuthenticationError("SFTP 私钥格式无效")

    def _connect(self, target: PublishTarget) -> tuple[Any, Any]:
        self.validate_target(target)
        module = self._paramiko()
        config = target.config or {}
        password = CredentialService.get_optional_secret(target.credential_ref, "password")
        private_key = CredentialService.get_optional_secret(target.credential_ref, "private_key")
        if not password and not private_key:
            raise PublishTargetConfigurationError(f"发布目标凭证未配置：{target.credential_ref}/password 或 private_key")
        client = self.client_factory() if self.client_factory else module.SSHClient()
        settings = get_settings()
        try:
            if hasattr(client, "load_system_host_keys"):
                client.load_system_host_keys()
            connect_kwargs: dict[str, object] = {
                "hostname": str(config["host"]),
                "port": int(config.get("port", 22)),
                "username": str(config["username"]),
                "password": password,
                "timeout": settings.publish_connection_timeout_seconds,
                "banner_timeout": settings.publish_connection_timeout_seconds,
                "auth_timeout": settings.publish_connection_timeout_seconds,
                "allow_agent": False,
                "look_for_keys": False,
            }
            if private_key:
                passphrase = CredentialService.get_optional_secret(target.credential_ref, "passphrase")
                connect_kwargs["pkey"] = self._private_key(module, private_key, passphrase)
            client.connect(**connect_kwargs)
            sftp = client.open_sftp()
            channel = sftp.get_channel() if hasattr(sftp, "get_channel") else None
            if channel and hasattr(channel, "settimeout"):
                channel.settimeout(settings.publish_operation_timeout_seconds)
            return client, sftp
        except PublishError:
            client.close()
            raise
        except getattr(module, "AuthenticationException", Exception) as exc:
            client.close()
            raise PublishAuthenticationError("SFTP 认证失败") from exc
        except (socket.timeout, TimeoutError) as exc:
            client.close()
            raise PublishTimeoutError("SFTP 连接超时") from exc
        except OSError as exc:
            client.close()
            raise PublishTargetConnectionError("SFTP 连接失败") from exc
        except Exception as exc:
            client.close()
            raise PublishTargetConnectionError("SFTP 连接失败") from exc

    @staticmethod
    def _ensure_directory(sftp: Any, path: str) -> None:
        current = "/" if path.startswith("/") else ""
        for part in PurePosixPath(path).parts:
            if part == "/":
                continue
            current = posixpath.join(current, part)
            try:
                sftp.stat(current)
            except OSError:
                sftp.mkdir(current)

    def publish(self, artifact: PublishArtifact, target: PublishTarget) -> TargetPublishResult:
        client, sftp = self._connect(target)
        config = target.config or {}
        remote_root = str(config["remote_root"]).rstrip("/")
        remote_path = posixpath.join(remote_root, artifact.generated_path)
        try:
            if artifact.is_directory:
                self._ensure_directory(sftp, remote_path)
                for local_file, relative in self.artifact_files(artifact):
                    remote_file = posixpath.join(remote_path, relative)
                    self._ensure_directory(sftp, posixpath.dirname(remote_file))
                    sftp.put(str(local_file), remote_file, confirm=True)
            else:
                self._ensure_directory(sftp, remote_root)
                sftp.put(str(artifact.local_path), remote_path, confirm=True)
        except PermissionError as exc:
            raise PublishPermissionError("SFTP 远程目录没有写入权限") from exc
        except (socket.timeout, TimeoutError) as exc:
            raise PublishTimeoutError("SFTP 上传超时") from exc
        except OSError as exc:
            raise PublishUploadError("SFTP 上传失败") from exc
        finally:
            sftp.close()
            client.close()
        publish_url = (
            build_view_url(str(config["base_url"]), artifact.generated_path)
            if artifact.is_directory
            else build_file_url(str(config["base_url"]), artifact.local_path.name)
        )
        return TargetPublishResult(True, publish_url, remote_path, "SFTP 发布成功")

    def test_connection(self, target: PublishTarget) -> bool:
        client, sftp = self._connect(target)
        try:
            config = target.config or {}
            sftp.stat(str(config["remote_root"]))
            return True
        except PermissionError as exc:
            raise PublishPermissionError("SFTP 远程目录不可访问") from exc
        except OSError as exc:
            raise PublishTargetConnectionError("SFTP 远程目录不存在或不可访问") from exc
        finally:
            sftp.close()
            client.close()
