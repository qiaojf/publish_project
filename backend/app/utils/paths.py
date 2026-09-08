from pathlib import Path

from app.core.config import PROJECT_ROOT
from app.core.exceptions import PublishError


def safe_child(root: Path, *parts: str) -> Path:
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    if not candidate.is_relative_to(resolved_root):
        raise PublishError("生成的文件路径超出允许目录")
    return candidate


def resolve_publish_root(value: str) -> Path:
    raw = Path(value)
    root = raw if raw.is_absolute() else PROJECT_ROOT / raw
    return root.resolve()


def build_view_url(base_url: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").strip("/")
    return f"{base_url.rstrip('/')}/{normalized}/"
