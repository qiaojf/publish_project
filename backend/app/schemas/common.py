from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = ""


class PageResult(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
