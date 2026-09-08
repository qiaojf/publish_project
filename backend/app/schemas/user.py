from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import UserRole, UserStatus


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    role: UserRole = UserRole.EMPLOYEE
    status: UserStatus = UserStatus.ACTIVE

    @field_validator("username", "name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("department")
    @classmethod
    def normalize_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(UserBase):
    password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("password", mode="before")
    @classmethod
    def empty_password_means_unchanged(cls, value: object) -> object:
        return None if value == "" else value


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class CurrentUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    name: str
    department: str | None = None
    role: UserRole
    status: UserStatus
