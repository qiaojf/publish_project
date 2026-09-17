from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str
    status_code: int = 400
    error_code: str | None = None

    def __str__(self) -> str:
        return self.message


class AuthenticationError(AppError):
    def __init__(self, message: str = "认证失败", error_code: str = "AUTH_UNAUTHORIZED") -> None:
        super().__init__(message, 401, error_code)


class PermissionDenied(AppError):
    def __init__(self, message: str = "没有权限执行该操作", error_code: str = "AUTH_FORBIDDEN") -> None:
        super().__init__(message, 403, error_code)


class ResourceNotFound(AppError):
    def __init__(self, message: str = "资源不存在", error_code: str | None = None) -> None:
        super().__init__(message, 404, error_code)


class BusinessRuleError(AppError):
    def __init__(self, message: str, status_code: int = 409, error_code: str | None = None) -> None:
        super().__init__(message, status_code, error_code)


class InvalidFileError(AppError):
    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message, 422, error_code)


class PublishError(AppError):
    def __init__(self, message: str, error_code: str | None = "PUBLISH_FAILED") -> None:
        super().__init__(message, 500, error_code)


class PublishTargetConfigurationError(PublishError):
    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message, error_code)


class PublishTargetConnectionError(PublishError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PUBLISH_CONNECTION_FAILED")


class PublishAuthenticationError(PublishError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PUBLISH_AUTHENTICATION_FAILED")


class PublishPermissionError(PublishError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PUBLISH_FAILED")


class PublishUploadError(PublishError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "UPLOAD_FAILED")


class PublishTimeoutError(PublishError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "PUBLISH_CONNECTION_FAILED")
