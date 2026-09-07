import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, categories, contents, dashboard, health, logs, publish_records, publish_targets, reviews, search, users
from app.core.config import get_settings
from app.core.exceptions import AppError


logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="公司内部内容提交、审核与自动发布平台 REST API",
    debug=settings.debug,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"success": False, "data": None, "message": exc.message})


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    return JSONResponse(status_code=exc.status_code, content={"success": False, "data": None, "message": message}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else None
    message = first.get("msg", "请求参数不正确") if first else "请求参数不正确"
    return JSONResponse(status_code=422, content={"success": False, "data": None, "message": message})


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", exc_info=exc)
    message = str(exc) if settings.debug else "服务器内部错误"
    return JSONResponse(status_code=500, content={"success": False, "data": None, "message": message})


api_prefix = "/api"
for route in (health.router, auth.router, users.router, categories.router, contents.router, reviews.router, publish_targets.router, publish_records.router, search.router, logs.router, dashboard.router):
    app.include_router(route, prefix=api_prefix)

if settings.app_env == "development":
    settings.local_published_root.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/local-published",
        StaticFiles(directory=settings.local_published_root, check_dir=False, html=True),
        name="local-published",
    )
