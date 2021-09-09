import scrapy


class BaseAirItem(scrapy.Item):
    pass


class ExportFinalData(BaseAirItem):
    pass


class ExportErrorData(BaseAirItem):
    status = scrapy.Field()
    detail = scrapy.Field()
    traceback_info = scrapy.Field()


class DebugItem(BaseAirItem):
    info = scrapy.Field()
