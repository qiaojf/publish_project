from pathlib import Path

import pytest

from app.db.models.content import Content
from app.db.models.publish_target import PublishTarget
from app.publishers.dynamic import DynamicPagePublisher
from app.publishers.excel import ExcelPublisher
from app.publishers.file import FilePublisher
from app.publishers.html import HtmlPublisher
from app.publishers.image import ImagePublisher
from app.publishers.pdf import PdfPublisher
from app.publishers.ppt import PptPublisher
from app.publishers.word import WordPublisher


def make_target(tmp_path: Path, content_type: str) -> PublishTarget:
    return PublishTarget(id=1, name="target", content_types=[content_type], publish_root=str(tmp_path), base_url="https://internal.example/content/", enabled=True, created_by=1)


def test_html_and_dynamic_publishers(tmp_path: Path) -> None:
    html_content = Content(id=11, title="HTML 页面", content_type="html", content_body="<h1>hello</h1>", created_by=1)
    html_result = HtmlPublisher().publish(html_content, make_target(tmp_path / "html", "html"))
    assert Path(html_result.output_path, "index.html").read_text(encoding="utf-8") == "<h1>hello</h1>"
    dynamic_content = Content(id=12, title="动态 页面", content_type="dynamic", content_body="<main>dynamic</main>", created_by=1)
    dynamic_result = DynamicPagePublisher().publish(dynamic_content, make_target(tmp_path / "dynamic", "dynamic"))
    assert "dynamic" in Path(dynamic_result.output_path, "index.html").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("publisher", "content_type", "extension"),
    [(PptPublisher, "ppt", ".pptx"), (PdfPublisher, "pdf", ".pdf"), (WordPublisher, "word", ".docx"),
     (ExcelPublisher, "excel", ".xlsx"), (ImagePublisher, "image", ".png"), (FilePublisher, "file", ".zip")],
)
def test_asset_publishers(tmp_path: Path, publisher, content_type: str, extension: str) -> None:
    source = tmp_path / f"source{extension}"
    source.write_bytes(b"source bytes")
    content = Content(id=20, title="Asset", content_type=content_type, source_file_name=source.name, source_file_path=str(source), created_by=1)
    result = publisher().publish(content, make_target(tmp_path / f"out-{content_type}", content_type))
    assert Path(result.output_path, "index.html").is_file()
    assert list(Path(result.output_path, "files").iterdir())
    assert result.view_url.startswith("https://internal.example/content/20-asset/")
