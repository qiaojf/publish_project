from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import CategoryVisibility


class CategoryPayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    enabled: bool = True
    sort_order: int = Field(default=0, ge=0, le=9999)
    visibility_scope: CategoryVisibility = CategoryVisibility.ALL
    department: str | None = Field(default=None, max_length=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("分类名称不能为空")
        return normalized

    @field_validator("department")
    @classmethod
    def normalize_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_visibility(self) -> "CategoryPayload":
        if self.visibility_scope == CategoryVisibility.DEPARTMENT and not self.department:
            raise ValueError("部门可见时必须选择所属部门")
        if self.visibility_scope != CategoryVisibility.DEPARTMENT:
            self.department = None
        return self


class CategoryStatusUpdate(BaseModel):
    enabled: bool


class CategoryRead(CategoryPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
