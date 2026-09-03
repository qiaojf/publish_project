from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


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
