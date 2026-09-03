from __future__ import annotations

import html
import re
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_PREVIEW_ROWS = 200
MAX_PREVIEW_COLUMNS = 50
MAX_PREVIEW_SLIDES = 100


def _read_member(archive: ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > MAX_MEMBER_BYTES:
        raise ValueError("文档内容过大，无法在线展开")
    return archive.read(info)


def _xml(archive: ZipFile, name: str) -> ElementTree.Element:
    return ElementTree.fromstring(_read_member(archive, name))


def _shell(body: str, extra_css: str = "") -> str:
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
*{{box-sizing:border-box}}body{{margin:0;padding:28px 34px;color:#222;background:#fff;font:14px/1.75 'Helvetica Neue','Microsoft YaHei',Arial,sans-serif}}
p{{margin:0 0 10px}}.empty{{color:#777}}{extra_css}
</style></head><body>{body}</body></html>"""


def _docx_preview(path: Path) -> str:
    with ZipFile(path) as archive:
        root = _xml(archive, "word/document.xml")
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t")).strip()
        if text:
            paragraphs.append(f"<p>{html.escape(text)}</p>")
    body = "".join(paragraphs) or '<p class="empty">文档中没有可提取的文字内容。</p>'
    return _shell(body, "p{max-width:900px}")


def _pptx_preview(path: Path) -> str:
    with ZipFile(path) as archive:
        slide_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=lambda value: int(re.search(r"\d+", Path(value).stem).group()),
        )[:MAX_PREVIEW_SLIDES]
        slides: list[str] = []
        namespace = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        for index, name in enumerate(slide_names, start=1):
            root = _xml(archive, name)
            lines = [node.text.strip() for node in root.iter(f"{namespace}t") if node.text and node.text.strip()]
            content = "".join(f"<p>{html.escape(line)}</p>" for line in lines) or '<p class="empty">本页没有文字内容。</p>'
            slides.append(f'<section class="slide"><span class="slide-no">{index:02d}</span><div>{content}</div></section>')
    body = "".join(slides) or '<p class="empty">演示文稿中没有可提取的幻灯片内容。</p>'
    css = ".slide{position:relative;min-height:220px;margin:0 auto 24px;padding:38px 46px;background:#fff;border:1px solid #ddd;box-shadow:0 8px 24px rgba(34,34,34,.08)}.slide-no{position:absolute;right:18px;bottom:12px;color:#81b119;font:11px Montserrat,Arial,sans-serif}.slide p:first-child{font-size:24px;font-weight:650;line-height:1.35}.slide p{margin:0 0 12px}"
    return _shell(body, css)


def _cell_text(cell: ElementTree.Element, shared: list[str], namespace: str) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{namespace}t"))
    value = cell.find(f"{namespace}v")
    raw = value.text if value is not None and value.text is not None else ""
    if cell_type == "s" and raw.isdigit():
        index = int(raw)
        return shared[index] if index < len(shared) else raw
    if cell_type == "b":
        return "是" if raw == "1" else "否"
    return raw


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    result = 0
    for letter in letters.group() if letters else "A":
        result = result * 26 + ord(letter) - 64
    return max(0, result - 1)


def _xlsx_preview(path: Path) -> str:
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = _xml(archive, "xl/sharedStrings.xml")
            shared = ["".join(node.text or "" for node in item.iter(f"{namespace}t")) for item in shared_root.iter(f"{namespace}si")]
        sheet_names = sorted(
            (name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)),
            key=lambda value: int(re.search(r"\d+", Path(value).stem).group()),
        )[:5]
        sheets: list[str] = []
        for sheet_index, name in enumerate(sheet_names, start=1):
            root = _xml(archive, name)
            rows: list[str] = []
            for row in list(root.iter(f"{namespace}row"))[:MAX_PREVIEW_ROWS]:
                values: dict[int, str] = {}
                for cell in row.iter(f"{namespace}c"):
                    column = _column_index(cell.attrib.get("r", "A1"))
                    if column < MAX_PREVIEW_COLUMNS:
                        values[column] = _cell_text(cell, shared, namespace)
                if values:
                    cells = "".join(f"<td>{html.escape(values.get(column, ''))}</td>" for column in range(max(values) + 1))
                    rows.append(f"<tr>{cells}</tr>")
            table = f"<table>{''.join(rows)}</table>" if rows else '<p class="empty">工作表中没有可显示的数据。</p>'
            sheets.append(f'<section><h2>工作表 {sheet_index}</h2><div class="table-wrap">{table}</div></section>')
    body = "".join(sheets) or '<p class="empty">工作簿中没有可提取的工作表。</p>'
    css = "section+section{margin-top:32px}h2{margin:0 0 12px;color:#648f0e;font-size:16px}.table-wrap{overflow:auto;border:1px solid #ddd}table{border-collapse:collapse;min-width:100%}td{min-width:110px;padding:8px 10px;border:1px solid #e5e5e5;white-space:nowrap}tr:first-child td{background:#f2f7e8;font-weight:650}"
    return _shell(body, css)


def build_document_preview(path: Path, content_type: str) -> str | None:
    try:
        if content_type == "word" and path.suffix.lower() == ".docx":
            return _docx_preview(path)
        if content_type == "ppt" and path.suffix.lower() == ".pptx":
            return _pptx_preview(path)
        if content_type == "excel" and path.suffix.lower() == ".xlsx":
            return _xlsx_preview(path)
    except (BadZipFile, KeyError, ElementTree.ParseError, OSError, ValueError):
        return None
    return None
