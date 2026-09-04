from app.core.constants import PublishTargetType
from app.core.exceptions import PublishTargetConfigurationError
from app.target_publishers.base import BaseTargetPublisher
from app.target_publishers.dropbox import DropboxTargetPublisher
from app.target_publishers.github import GitHubTargetPublisher
from app.target_publishers.github_pages import GitHubPagesTargetPublisher
from app.target_publishers.local import LocalTargetPublisher
from app.target_publishers.onedrive import OneDriveTargetPublisher
from app.target_publishers.sftp import SftpTargetPublisher


class TargetPublisherFactory:
    _publishers: dict[PublishTargetType, type[BaseTargetPublisher]] = {
        PublishTargetType.LOCAL: LocalTargetPublisher,
        PublishTargetType.SFTP: SftpTargetPublisher,
        PublishTargetType.GITHUB: GitHubTargetPublisher,
        PublishTargetType.GITHUB_PAGES: GitHubPagesTargetPublisher,
        PublishTargetType.ONEDRIVE: OneDriveTargetPublisher,
        PublishTargetType.DROPBOX: DropboxTargetPublisher,
    }

    @classmethod
    def create(cls, target_type: str) -> BaseTargetPublisher:
        try:
            return cls._publishers[PublishTargetType(target_type)]()
        except (KeyError, ValueError) as exc:
            raise PublishTargetConfigurationError(f"不支持的发布目标类型：{target_type}") from exc
