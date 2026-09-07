from pathlib import Path

from app.content_processors.html import HtmlContentProcessor
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

        assert (artifact.local_path / "index.html").read_text(encoding="utf-8") == "<h1>uploaded page</h1>"
    finally:
        settings.source_storage_root = original_source
        settings.build_storage_root = original_build
