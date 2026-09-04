from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Internal Content Publish Platform"
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    database_url: str = "postgresql+psycopg://postgres:password@localhost:5432/content_publish"
    test_database_url: str = "postgresql+psycopg://postgres:password@localhost:5432/content_publish_test"
    jwt_secret_key: str = "change-this-in-production-use-at-least-32-characters"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=480, gt=0)
    source_storage_root: Path = Path("./storage/source")
    preview_storage_root: Path = Path("./storage/preview")
    build_storage_root: Path = Path("../local-data/build")
    local_published_root: Path = Path("../local-data/published")
    local_published_base_url: str = "http://localhost:8000/local-published"
    max_upload_size_mb: int = Field(default=100, gt=0, le=1024)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    db_connect_timeout_seconds: int = Field(default=5, gt=0, le=60)
    db_pool_size: int = Field(default=10, gt=0)
    db_max_overflow: int = Field(default=20, ge=0)
    publish_connection_timeout_seconds: int = Field(default=30, gt=0, le=300)
    publish_operation_timeout_seconds: int = Field(default=300, gt=0, le=3600)
    seed_admin_password: str = "admin123"
    seed_employee_password: str = "employee123"

    @field_validator("database_url", "test_database_url")
    @classmethod
    def validate_postgresql_url(cls, value: str) -> str:
        if not value.startswith("postgresql+psycopg://"):
            raise ValueError("Only PostgreSQL with psycopg 3 is supported")
        return value

    @field_validator("source_storage_root", "preview_storage_root", "build_storage_root", "local_published_root", mode="after")
    @classmethod
    def resolve_storage_path(cls, value: Path) -> Path:
        return value.resolve() if value.is_absolute() else (BACKEND_ROOT / value).resolve()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
