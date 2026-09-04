from app.target_publishers.dropbox import DropboxTargetPublisher
from app.target_publishers.factory import TargetPublisherFactory
from app.target_publishers.github import GitHubTargetPublisher
from app.target_publishers.github_pages import GitHubPagesTargetPublisher
from app.target_publishers.local import LocalTargetPublisher
from app.target_publishers.onedrive import OneDriveTargetPublisher
from app.target_publishers.sftp import SftpTargetPublisher


def test_target_publisher_factory_maps_every_supported_type() -> None:
    expected = {
        "local": LocalTargetPublisher,
        "sftp": SftpTargetPublisher,
        "github": GitHubTargetPublisher,
        "github_pages": GitHubPagesTargetPublisher,
        "onedrive": OneDriveTargetPublisher,
        "dropbox": DropboxTargetPublisher,
    }
    for target_type, publisher_class in expected.items():
        assert isinstance(TargetPublisherFactory.create(target_type), publisher_class)
