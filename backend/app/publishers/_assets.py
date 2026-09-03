import html
import shutil
from pathlib import Path

from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.db.models.publish_target import PublishTarget
from app.publishers.base import BasePublisher, PublishResult
from app.utils.paths import safe_child


class AssetPagePublisher(BasePublisher):
    heading = "内容文件"
    description = "点击下方按钮查看或下载原始文件。"
    embed_template: str | None = None

    def publish(self, content: Content, target: PublishTarget) -> PublishResult:
        if not content.source_file_path or not Path(content.source_file_path).is_file():
            raise PublishError("源文件不存在，无法发布")
        relative_path, output_dir, view_url = self.prepare_output(content, target)
        files_dir = safe_child(output_dir, "files")
        files_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"source{Path(content.source_file_name or content.source_file_path).suffix.lower()}"
        output_file = safe_child(files_dir, safe_name)
        shutil.copy2(content.source_file_path, output_file)
        file_url = f"files/{safe_name}"
        embedded = self.embed_template.format(url=html.escape(file_url)) if self.embed_template else ""
        page = self._page(content, file_url, embedded)
        safe_child(output_dir, "index.html").write_text(page, encoding="utf-8")
        return PublishResult(relative_path, str(output_dir), view_url)

    def _page(self, content: Content, file_url: str, embedded: str) -> str:
        return f"""<!doctype html>
<html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{html.escape(content.title)}</title><style>body{{font-family:system-ui,sans-serif;max-width:1080px;margin:48px auto;padding:0 24px;color:#172033}}p{{color:#667085;line-height:1.8}}a{{display:inline-block;margin:18px 0;padding:10px 18px;background:#315b8a;color:#fff;text-decoration:none}}iframe,object,img{{width:100%;min-height:70vh;border:1px solid #dce1e8;object-fit:contain}}</style></head>
<body><h1>{html.escape(content.title)}</h1><p>{html.escape(content.description or self.description)}</p><a href=\"{html.escape(file_url)}\">查看 / 下载原始文件</a>{embedded}</body></html>"""
