import shutil
from pathlib import Path

from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.db.models.publish_target import PublishTarget
from app.publishers.base import BasePublisher, PublishResult
from app.utils.paths import safe_child


class HtmlPublisher(BasePublisher):
    def publish(self, content: Content, target: PublishTarget) -> PublishResult:
        relative_path, output_dir, view_url = self.prepare_output(content, target)
        index_file = safe_child(output_dir, "index.html")
        if content.content_body:
            index_file.write_text(content.content_body, encoding="utf-8")
        elif content.source_file_path and Path(content.source_file_path).is_file():
            shutil.copy2(content.source_file_path, index_file)
        else:
            raise PublishError("HTML 内容或源文件不存在")
        return PublishResult(relative_path, str(output_dir), view_url)
