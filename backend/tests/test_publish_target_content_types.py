import pytest
from pydantic import ValidationError

from app.core.constants import ContentType
from app.schemas.publish_target import PublishTargetPayload


ALL_TYPES = [item.value for item in ContentType]


@pytest.mark.parametrize(
    ("target_type", "fields"),
    (
        ("local", {"publish_root": "/srv/content", "base_url": "https://content.example.com/"}),
        ("sftp", {"config": {"host": "server", "port": 22, "username": "publisher", "remote_root": "/srv/content", "base_url": "https://content.example.com/"}, "credential_ref": "sftp_company"}),
        ("github", {"config": {"owner": "company", "repo": "content", "branch": "main", "repo_path": "published"}, "credential_ref": "github_company"}),
        ("onedrive", {"config": {"tenant_id": "tenant", "client_id": "client", "drive_id": "drive", "folder_path": "/Published"}, "credential_ref": "onedrive_company"}),
        ("dropbox", {"config": {"folder_path": "/Published"}, "credential_ref": "dropbox_company"}),
    ),
)
def test_file_storage_targets_allow_all_content_types(target_type: str, fields: dict[str, object]) -> None:
    payload = PublishTargetPayload(
        name="综合发布区", target_type=target_type, content_types=ALL_TYPES, **fields,
    )
    assert {item.value for item in payload.content_types} == set(ALL_TYPES)


def test_github_pages_allows_static_types_but_rejects_dynamic_pages() -> None:
    fields = {
        "name": "Pages",
        "target_type": "github_pages",
        "config": {
            "owner": "company", "repo": "content", "branch": "gh-pages",
            "repo_path": "published", "base_url": "https://company.github.io/content/",
        },
        "credential_ref": "github_pages_company",
    }
    static_types = [item for item in ALL_TYPES if item != "dynamic"]
    payload = PublishTargetPayload(content_types=static_types, **fields)
    assert {item.value for item in payload.content_types} == set(static_types)
    with pytest.raises(ValidationError, match="仅支持静态内容"):
        PublishTargetPayload(content_types=ALL_TYPES, **fields)
