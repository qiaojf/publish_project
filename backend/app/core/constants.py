from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class CategoryVisibility(StrEnum):
    PUBLISHER = "publisher"
    DEPARTMENT = "department"
    ALL = "all"


class ContentType(StrEnum):
    HTML = "html"
    DYNAMIC = "dynamic"
    PPT = "ppt"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    IMAGE = "image"
    FILE = "file"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PublishStatus(StrEnum):
    UNPUBLISHED = "unpublished"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class ReviewAction(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"


class PublishRecordStatus(StrEnum):
    PUBLISHING = "publishing"
    SUCCESS = "success"
    FAILED = "failed"


class PublishTargetType(StrEnum):
    LOCAL = "local"
    SFTP = "sftp"
    GITHUB = "github"
    GITHUB_PAGES = "github_pages"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"


ALL_PUBLISHABLE_CONTENT_TYPES = frozenset(ContentType)
PUBLISH_TARGET_CONTENT_TYPES: dict[PublishTargetType, frozenset[ContentType]] = {
    PublishTargetType.LOCAL: ALL_PUBLISHABLE_CONTENT_TYPES,
    PublishTargetType.SFTP: ALL_PUBLISHABLE_CONTENT_TYPES,
    PublishTargetType.GITHUB: ALL_PUBLISHABLE_CONTENT_TYPES,
    PublishTargetType.GITHUB_PAGES: ALL_PUBLISHABLE_CONTENT_TYPES - {ContentType.DYNAMIC},
    PublishTargetType.ONEDRIVE: ALL_PUBLISHABLE_CONTENT_TYPES,
    PublishTargetType.DROPBOX: ALL_PUBLISHABLE_CONTENT_TYPES,
}


ALLOWED_EXTENSIONS: dict[ContentType, set[str]] = {
    ContentType.HTML: {".html", ".htm"},
    ContentType.DYNAMIC: {".html", ".htm", ".zip"},
    ContentType.PPT: {".ppt", ".pptx"},
    ContentType.PDF: {".pdf"},
    ContentType.WORD: {".doc", ".docx"},
    ContentType.EXCEL: {".xls", ".xlsx"},
    ContentType.IMAGE: {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"},
    ContentType.FILE: set(),
}
