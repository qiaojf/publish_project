from app.content_processors.base import BaseContentProcessor
from app.content_processors.dynamic import DynamicContentProcessor
from app.content_processors.excel import ExcelContentProcessor
from app.content_processors.file import FileContentProcessor
from app.content_processors.html import HtmlContentProcessor
from app.content_processors.image import ImageContentProcessor
from app.content_processors.pdf import PdfContentProcessor
from app.content_processors.ppt import PptContentProcessor
from app.content_processors.word import WordContentProcessor
from app.core.constants import ContentType
from app.core.exceptions import PublishError


class ContentProcessorFactory:
    _processors: dict[ContentType, type[BaseContentProcessor]] = {
        ContentType.HTML: HtmlContentProcessor,
        ContentType.DYNAMIC: DynamicContentProcessor,
        ContentType.PPT: PptContentProcessor,
        ContentType.PDF: PdfContentProcessor,
        ContentType.WORD: WordContentProcessor,
        ContentType.EXCEL: ExcelContentProcessor,
        ContentType.IMAGE: ImageContentProcessor,
        ContentType.FILE: FileContentProcessor,
    }

    @classmethod
    def create(cls, content_type: str) -> BaseContentProcessor:
        try:
            return cls._processors[ContentType(content_type)]()
        except (KeyError, ValueError) as exc:
            raise PublishError(f"不支持的内容类型：{content_type}") from exc
