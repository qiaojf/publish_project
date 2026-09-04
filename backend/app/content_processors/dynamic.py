import html

from app.content_processors.base import BaseContentProcessor
from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.target_publishers.base import PublishArtifact
from app.utils.paths import safe_child


class DynamicContentProcessor(BaseContentProcessor):
    def process(self, content: Content) -> PublishArtifact:
        if not content.content_body:
            raise PublishError("动态页面内容不能为空")
        output = self.prepare_output(content)
        page = content.content_body
        if "<html" not in page.lower():
            page = f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>{html.escape(content.title)}</title></head><body>{page}</body></html>"
        safe_child(output, "index.html").write_text(page, encoding="utf-8")
        return PublishArtifact(output, "index.html", content.content_type, True)
