from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.config import get_settings
from app.target_publishers.base import PublishArtifact
from app.utils.paths import safe_child


class ArtifactPackagingService:
    @staticmethod
    def package_directory(artifact: PublishArtifact) -> Path:
        if not artifact.is_directory:
            return artifact.local_path
        package_root = safe_child(get_settings().build_storage_root, "_packages")
        package_root.mkdir(parents=True, exist_ok=True)
        archive = safe_child(package_root, f"{artifact.local_path.name}.zip")
        archive.unlink(missing_ok=True)
        with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
            for source in sorted(path for path in artifact.local_path.rglob("*") if path.is_file()):
                bundle.write(source, source.relative_to(artifact.local_path).as_posix())
        return archive
