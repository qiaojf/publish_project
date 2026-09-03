from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


class AuthenticationError(AppError):
    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message, 401)


class PermissionDenied(AppError):
    def __init__(self, message: str = "没有权限执行该操作") -> None:
        super().__init__(message, 403)


class ResourceNotFound(AppError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, 404)


class BusinessRuleError(AppError):
    def __init__(self, message: str, status_code: int = 409) -> None:
        super().__init__(message, status_code)


class InvalidFileError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, 422)


class PublishError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, 500)
