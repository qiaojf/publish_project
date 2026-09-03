from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=ApiResponse[dict[str, str]], summary="健康检查")
def health(db: DbSession) -> ApiResponse[dict[str, str]]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL 数据库不可用",
        ) from exc
    return ApiResponse(data={"status": "ok"})
