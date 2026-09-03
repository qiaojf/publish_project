from app.publishers._assets import AssetPagePublisher


class ImagePublisher(AssetPagePublisher):
    heading = "图片资源"
    embed_template = '<img src="{url}" alt="图片内容">'
