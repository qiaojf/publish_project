from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.schemas.common import ApiResponse


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=ApiResponse[dict[str, str]], summary="健康检查")
def health(db: DbSession) -> ApiResponse[dict[str, str]]:
    try:
        db.execute(text(
            "SELECT id, name, enabled, sort_order, visibility_scope, department, created_at, updated_at "
            "FROM categories LIMIT 1"
        ))
        db.execute(text("SELECT department FROM users LIMIT 1"))
        db.execute(text("SELECT id, name, enabled, sort_order, created_at, updated_at FROM departments LIMIT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL 数据库不可用或数据库结构未更新，请执行 alembic upgrade head",
        ) from exc
    return ApiResponse(data={"status": "ok"})
