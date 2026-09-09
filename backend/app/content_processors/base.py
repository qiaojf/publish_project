import html
import shutil
from abc import ABC, abstractmethod
from pathlib import Path, PurePosixPath

from app.core.config import get_settings
from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.target_publishers.base import PublishArtifact
from app.utils.paths import safe_child
from app.utils.slug import safe_slug


class BaseContentProcessor(ABC):
    @abstractmethod
    def process(self, content: Content) -> PublishArtifact:
        raise NotImplementedError

    @staticmethod
    def prepare_output(content: Content) -> Path:
        root = get_settings().build_storage_root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        output = safe_child(root, f"{content.id}-{safe_slug(content.title)}")
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True, exist_ok=False)
        return output

    @staticmethod
    def source_files(content: Content) -> list[tuple[Path, str]]:
        if not content.source_file_path:
            return []
        source = Path(content.source_file_path).resolve()
        storage_root = get_settings().source_storage_root.resolve()
        if not source.is_relative_to(storage_root) or not source.exists():
            raise PublishError("源文件不存在，无法发布")
        metadata = content.source_files or []
        if source.is_file():
            return [(source, content.source_file_name or source.name)]
        entries: list[tuple[Path, str]] = []
        for item in metadata:
            relative = str(item.get("relative_path") or item.get("name") or "").replace("\\", "/").strip("/")
            parts = PurePosixPath(relative).parts
            if not relative or any(part in {"", ".", ".."} for part in parts):
                raise PublishError("源文件清单包含不安全路径")
            candidate = source.joinpath(*parts).resolve()
            if not candidate.is_relative_to(source) or not candidate.is_file():
                raise PublishError(f"源文件不存在：{relative}")
            entries.append((candidate, PurePosixPath(relative).as_posix()))
        if not entries:
            entries = [
                (candidate, candidate.relative_to(source).as_posix())
                for candidate in sorted(item for item in source.rglob("*") if item.is_file())
            ]
        return entries


class AssetPageContentProcessor(BaseContentProcessor):
    heading = "内容文件"
    description = "点击文件名查看或下载原始文件。"
    embed_kind: str | None = None

    def process(self, content: Content) -> PublishArtifact:
        sources = self.source_files(content)
        if not sources:
            raise PublishError("源文件不存在，无法发布")
        if len(sources) == 1 and not content.source_is_directory:
            source, relative = sources[0]
            file_name = PurePosixPath(relative).name
            return PublishArtifact(source, file_name, content.content_type, False, ((source, file_name),))
        output = self.prepare_output(content)
        files_root = safe_child(output, "files")
        files_root.mkdir(parents=True, exist_ok=True)
        published: list[str] = []
        for source, relative in sources:
            destination = safe_child(files_root, *PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            published.append(f"files/{PurePosixPath(relative).as_posix()}")
        safe_links = "".join(
            f'<li><a href="{html.escape(path)}">{html.escape(path.removeprefix("files/"))}</a></li>'
            for path in published
        )
        embedded = ""
        if len(published) == 1 and self.embed_kind == "pdf":
            embedded = f'<object data="{html.escape(published[0])}" type="application/pdf"><a href="{html.escape(published[0])}">打开 PDF</a></object>'
        elif len(published) == 1 and self.embed_kind == "image":
            embedded = f'<img src="{html.escape(published[0])}" alt="图片内容">'
        page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(content.title)}</title><style>body{{font-family:system-ui,sans-serif;max-width:1080px;margin:48px auto;padding:0 24px;color:#172033}}p{{color:#667085;line-height:1.8}}ul{{padding:0;list-style:none}}li{{border-bottom:1px solid #e5e7eb}}a{{display:block;padding:12px 0;color:#315b8a;text-decoration:none}}object,img{{width:100%;min-height:70vh;border:1px solid #dce1e8;object-fit:contain}}</style></head>
<body><h1>{html.escape(content.title)}</h1><p>{html.escape(content.description or self.description)}</p><h2>{html.escape(self.heading)}</h2><ul>{safe_links}</ul>{embedded}</body></html>"""
        safe_child(output, "index.html").write_text(page, encoding="utf-8")
        return PublishArtifact(output, "index.html", content.content_type, True, tuple(sources))
