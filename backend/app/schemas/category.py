from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    enabled: bool = True
    sort_order: int = Field(default=0, ge=0, le=9999)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("分类名称不能为空")
        return normalized


class CategoryStatusUpdate(BaseModel):
    enabled: bool


class CategoryRead(CategoryPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
