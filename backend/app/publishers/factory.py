from app.core.constants import ContentType
from app.core.exceptions import PublishError
from app.publishers.base import BasePublisher
from app.publishers.dynamic import DynamicPagePublisher
from app.publishers.excel import ExcelPublisher
from app.publishers.file import FilePublisher
from app.publishers.html import HtmlPublisher
from app.publishers.image import ImagePublisher
from app.publishers.pdf import PdfPublisher
from app.publishers.ppt import PptPublisher
from app.publishers.word import WordPublisher


class PublisherFactory:
    _publishers: dict[ContentType, type[BasePublisher]] = {
        ContentType.HTML: HtmlPublisher,
        ContentType.DYNAMIC: DynamicPagePublisher,
        ContentType.PPT: PptPublisher,
        ContentType.PDF: PdfPublisher,
        ContentType.WORD: WordPublisher,
        ContentType.EXCEL: ExcelPublisher,
        ContentType.IMAGE: ImagePublisher,
        ContentType.FILE: FilePublisher,
    }

    @classmethod
    def create(cls, content_type: str) -> BasePublisher:
        try:
            return cls._publishers[ContentType(content_type)]()
        except (KeyError, ValueError) as exc:
            raise PublishError(f"不支持的内容类型：{content_type}") from exc
