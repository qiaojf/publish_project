import html

from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.db.models.publish_target import PublishTarget
from app.publishers.base import BasePublisher, PublishResult
from app.utils.paths import safe_child


class DynamicPagePublisher(BasePublisher):
    def publish(self, content: Content, target: PublishTarget) -> PublishResult:
        if not content.content_body:
            raise PublishError("动态页面内容不能为空")
        relative_path, output_dir, view_url = self.prepare_output(content, target)
        page = f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><title>{html.escape(content.title)}</title></head><body>{content.content_body}</body></html>"
        safe_child(output_dir, "index.html").write_text(page, encoding="utf-8")
        return PublishResult(relative_path, str(output_dir), view_url)
