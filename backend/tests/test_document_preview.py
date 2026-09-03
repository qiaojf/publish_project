from pathlib import Path
from zipfile import ZipFile

from app.utils.document_preview import build_document_preview


def _write_zip(path: Path, members: dict[str, str]) -> Path:
    with ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def test_docx_preview_uses_document_text(tmp_path: Path) -> None:
    path = _write_zip(tmp_path / "demo.docx", {
        "word/document.xml": """<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>第一段正文</w:t></w:r></w:p><w:p><w:r><w:t>第二段正文</w:t></w:r></w:p></w:body></w:document>""",
    })
    preview = build_document_preview(path, "word")
    assert preview and "第一段正文" in preview and "第二段正文" in preview


def test_pptx_preview_uses_slide_text(tmp_path: Path) -> None:
    path = _write_zip(tmp_path / "demo.pptx", {
        "ppt/slides/slide1.xml": """<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><a:t>项目进展</a:t><a:t>完成首轮验证</a:t></p:cSld></p:sld>""",
    })
    preview = build_document_preview(path, "ppt")
    assert preview and "项目进展" in preview and "完成首轮验证" in preview


def test_xlsx_preview_uses_cell_values(tmp_path: Path) -> None:
    path = _write_zip(tmp_path / "demo.xlsx", {
        "xl/sharedStrings.xml": """<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>区域</t></si><si><t>东部</t></si></sst>""",
        "xl/worksheets/sheet1.xml": """<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>120</v></c></row><row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>116</v></c></row></sheetData></worksheet>""",
    })
    preview = build_document_preview(path, "excel")
    assert preview and "区域" in preview and "东部" in preview and "116" in preview


def test_invalid_office_file_falls_back_without_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.pptx"
    path.write_bytes(b"not a zip")
    assert build_document_preview(path, "ppt") is None
