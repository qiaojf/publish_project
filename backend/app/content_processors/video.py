from pathlib import PurePosixPath

from app.content_processors.base import BaseContentProcessor
from app.core.exceptions import PublishError
from app.db.models.content import Content
from app.target_publishers.base import PublishArtifact


class VideoContentProcessor(BaseContentProcessor):
    def process(self, content: Content) -> PublishArtifact:
        sources = self.source_files(content)
        if len(sources) != 1 or content.source_is_directory:
            raise PublishError("视频内容必须只上传一个 MP4 或 MOV 文件")
        source, relative = sources[0]
        file_name = PurePosixPath(relative).name
        return PublishArtifact(
            source,
            file_name,
            content.content_type,
            False,
            ((source, file_name),),
            content.title,
            content.description,
        )
