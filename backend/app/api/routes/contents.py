from typing import Annotated

import mimetypes

from fastapi import APIRouter, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.constants import ContentType, PublishStatus, ReviewStatus
from app.schemas.common import ApiResponse, PageResult
from app.schemas.content import ContentPayload, ContentPreview, ContentRead
from app.services.content_service import ContentService
from app.services.publish_service import PublishService


router = APIRouter(prefix="/contents", tags=["Contents"])


@router.get("", response_model=ApiResponse[PageResult[ContentRead]], summary="内容列表")
def list_contents(
    db: DbSession, current_user: CurrentUser, keyword: str | None = None,
    content_type: ContentType | None = None, category: str | None = None,
    review_status: ReviewStatus | None = None, publish_status: PublishStatus | None = None,
    created_by: int | None = None, page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[PageResult[ContentRead]]:
    return ApiResponse(data=ContentService.list(
        db, current_user, keyword=keyword, content_type=content_type.value if content_type else None,
        category=category, review_status=review_status.value if review_status else None,
        publish_status=publish_status.value if publish_status else None, created_by=created_by,
        page=page, page_size=page_size,
    ))


def _payload(
    title: str, description: str | None, category: str | None, content_type: ContentType,
    publish_target_id: int | None, content_body: str | None,
) -> ContentPayload:
    return ContentPayload(title=title, description=description, category=category, content_type=content_type, publish_target_id=publish_target_id, content_body=content_body)


def _uploads(
    file: UploadFile | None, files: list[UploadFile] | None, file_paths: list[str] | None,
) -> tuple[list[UploadFile], list[str]]:
    uploads = list(files or [])
    paths = list(file_paths or [])
    if file:
        uploads.append(file)
        paths.append(file.filename or "")
    return uploads, paths


@router.post("", response_model=ApiResponse[ContentRead], status_code=status.HTTP_201_CREATED, summary="新建内容")
async def create_content(
    db: DbSession, current_user: CurrentUser, title: Annotated[str, Form()],
    content_type: Annotated[ContentType, Form()], description: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None, publish_target_id: Annotated[int | None, Form()] = None,
    content_body: Annotated[str | None, Form()] = None, file: Annotated[UploadFile | None, File()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
    file_paths: Annotated[list[str] | None, Form()] = None,
) -> ApiResponse[ContentRead]:
    uploads, paths = _uploads(file, files, file_paths)
    data = await ContentService.create(
        db, _payload(title, description, category, content_type, publish_target_id, content_body),
        uploads, paths, current_user,
    )
    return ApiResponse(data=data, message="内容已创建")


@router.get("/{content_id}", response_model=ApiResponse[ContentRead], summary="内容详情")
def get_content(content_id: int, db: DbSession, current_user: CurrentUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=ContentService.get(db, content_id, current_user))


@router.put("/{content_id}", response_model=ApiResponse[ContentRead], summary="更新内容")
async def update_content(
    content_id: int, db: DbSession, current_user: CurrentUser, title: Annotated[str, Form()],
    content_type: Annotated[ContentType, Form()], description: Annotated[str | None, Form()] = None,
    category: Annotated[str | None, Form()] = None, publish_target_id: Annotated[int | None, Form()] = None,
    content_body: Annotated[str | None, Form()] = None, file: Annotated[UploadFile | None, File()] = None,
    files: Annotated[list[UploadFile] | None, File()] = None,
    file_paths: Annotated[list[str] | None, Form()] = None,
) -> ApiResponse[ContentRead]:
    uploads, paths = _uploads(file, files, file_paths)
    data = await ContentService.update(
        db, content_id, _payload(title, description, category, content_type, publish_target_id, content_body),
        uploads, paths, current_user,
    )
    return ApiResponse(data=data, message="内容已更新")


@router.delete("/{content_id}", response_model=ApiResponse[dict[str, bool]], summary="逻辑删除内容")
def delete_content(content_id: int, db: DbSession, current_user: CurrentUser) -> ApiResponse[dict[str, bool]]:
    ContentService.delete(db, content_id, current_user)
    return ApiResponse(data={"deleted": True}, message="内容已删除")


@router.post("/{content_id}/submit", response_model=ApiResponse[ContentRead], summary="提交发布审核")
def submit_content(content_id: int, db: DbSession, current_user: CurrentUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=ContentService.submit(db, content_id, current_user), message="已提交发布审核")


@router.post("/{content_id}/publish", response_model=ApiResponse[ContentRead], summary="管理员直接发布")
def publish_content(content_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=PublishService.direct_publish(db, content_id, admin), message="发布流程已完成")


@router.post("/{content_id}/republish", response_model=ApiResponse[ContentRead], summary="重新发布失败内容")
def republish_content(content_id: int, db: DbSession, admin: AdminUser) -> ApiResponse[ContentRead]:
    return ApiResponse(data=PublishService.republish(db, content_id, admin), message="重新发布流程已完成")


@router.get("/{content_id}/preview", response_model=ApiResponse[ContentPreview], summary="获取安全预览信息")
def preview_content(content_id: int, db: DbSession, current_user: CurrentUser) -> ApiResponse[ContentPreview]:
    return ApiResponse(data=ContentService.preview(db, content_id, current_user))


@router.get("/{content_id}/preview/file", response_class=FileResponse, summary="读取预览源文件")
def preview_content_file(content_id: int, db: DbSession, current_user: CurrentUser) -> FileResponse:
    path, file_name = ContentService.preview_file(db, content_id, current_user)
    media_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=file_name, content_disposition_type="inline")


@router.get("/{content_id}/preview/files/{file_path:path}", response_class=FileResponse, summary="读取多文件内容中的源文件")
def preview_content_source_file(
    content_id: int, file_path: str, db: DbSession, current_user: CurrentUser,
) -> FileResponse:
    path, file_name = ContentService.preview_source_file(db, content_id, file_path, current_user)
    media_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=file_name, content_disposition_type="attachment")
