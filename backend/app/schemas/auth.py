from pydantic import BaseModel, Field

from app.schemas.user import CurrentUserRead


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class LoginResult(BaseModel):
    token: str
    user: CurrentUserRead
