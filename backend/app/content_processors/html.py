import shutil
from pathlib import Path, PurePosixPath

from app.content_processors.base import BaseContentProcessor
from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.target_publishers.base import PublishArtifact
from app.utils.paths import safe_child


class HtmlContentProcessor(BaseContentProcessor):
    def process(self, content: Content) -> PublishArtifact:
        output = self.prepare_output(content)
        body = content.content_body if content.content_body and content.content_body.strip().lower() != "null" else None
        if body:
            safe_child(output, "index.html").write_text(body, encoding="utf-8")
        else:
            sources = self.source_files(content)
            if not sources:
                raise PublishError("HTML 内容或源文件不存在")
            for source, relative in sources:
                destination = safe_child(output, *PurePosixPath(relative).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            html_files = [relative for _, relative in sources if Path(relative).suffix.lower() in {".html", ".htm"}]
            if "index.html" not in {path.lower() for path in html_files}:
                if len(html_files) != 1:
                    raise PublishError("HTML 文件夹必须包含 index.html")
                shutil.copy2(safe_child(output, *PurePosixPath(html_files[0]).parts), safe_child(output, "index.html"))
        return PublishArtifact(output, "index.html", content.content_type, True)
