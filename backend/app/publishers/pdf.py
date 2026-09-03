from app.publishers._assets import AssetPagePublisher


class PdfPublisher(AssetPagePublisher):
    heading = "PDF 文档"
    embed_template = '<object data="{url}" type="application/pdf"><a href="{url}">打开 PDF</a></object>'
