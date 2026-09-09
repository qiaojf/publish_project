from pathlib import Path

from app.content_processors.html import HtmlContentProcessor
from app.content_processors.image import ImageContentProcessor
from app.core.config import get_settings
from app.db.models.content import Content


def test_html_processor_ignores_legacy_null_body_and_uses_uploaded_file(tmp_path: Path) -> None:
    settings = get_settings()
    original_source = settings.source_storage_root
    original_build = settings.build_storage_root
    try:
        settings.source_storage_root = (tmp_path / "source").resolve()
        settings.build_storage_root = (tmp_path / "build").resolve()
        settings.source_storage_root.mkdir()
        source = settings.source_storage_root / "page.html"
        source.write_text("<h1>uploaded page</h1>", encoding="utf-8")
        content = Content(
            id=41, title="HTML 页面", content_type="html", content_body="null",
            source_file_name="page.html", source_file_path=str(source), created_by=1,
        )

        artifact = HtmlContentProcessor().process(content)

        assert artifact.local_path == source
        assert artifact.entry_file == "page.html"
        assert artifact.is_directory is False
        assert artifact.source_files == ((source, "page.html"),)
    finally:
        settings.source_storage_root = original_source
        settings.build_storage_root = original_build


def test_image_processor_keeps_single_uploaded_file_name(tmp_path: Path) -> None:
    settings = get_settings()
    original_source = settings.source_storage_root
    original_build = settings.build_storage_root
    try:
        settings.source_storage_root = (tmp_path / "source").resolve()
        settings.build_storage_root = (tmp_path / "build").resolve()
        settings.source_storage_root.mkdir()
        source = settings.source_storage_root / "src-montage.png"
        source.write_bytes(b"png")
        content = Content(
            id=42,
            title="图片",
            content_type="image",
            source_file_name=source.name,
            source_file_path=str(source),
            source_is_directory=False,
            created_by=1,
        )

        artifact = ImageContentProcessor().process(content)

        assert artifact.local_path == source
        assert artifact.is_directory is False
        assert artifact.source_files == ((source, "src-montage.png"),)
    finally:
        settings.source_storage_root = original_source
        settings.build_storage_root = original_build
