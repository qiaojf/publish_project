from app.content_processors.base import AssetPageContentProcessor


class PdfContentProcessor(AssetPageContentProcessor):
    heading = "PDF 文档"
    embed_kind = "pdf"
