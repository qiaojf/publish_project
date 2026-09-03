from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, LoginResult
from app.schemas.common import ApiResponse
from app.schemas.user import CurrentUserRead
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=ApiResponse[LoginResult], summary="用户名密码登录")
def login(payload: LoginRequest, request: Request, db: DbSession) -> ApiResponse[LoginResult]:
    ip_address = request.client.host if request.client else None
    return ApiResponse(data=AuthService.login(db, payload.username, payload.password, ip_address))


@router.post("/logout", response_model=ApiResponse[dict[str, bool]], summary="退出登录")
def logout(_current_user: CurrentUser) -> ApiResponse[dict[str, bool]]:
    return ApiResponse(data={"logged_out": True}, message="已退出登录")


@router.get("/me", response_model=ApiResponse[CurrentUserRead], summary="获取当前用户")
def me(current_user: CurrentUser) -> ApiResponse[CurrentUserRead]:
    return ApiResponse(data=CurrentUserRead.model_validate(current_user))
