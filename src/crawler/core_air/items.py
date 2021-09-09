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


class AirItem(BaseAirItem):
    task_id = scrapy.Field()
    mawb = scrapy.Field()
    origin = scrapy.Field()
    destination = scrapy.Field()
    pieces = scrapy.Field()
    weight = scrapy.Field()
    atd = scrapy.Field()
    ata = scrapy.Field()
    current_state = scrapy.Field()


class FlightItem(BaseAirItem):
    task_id = scrapy.Field()
    flight_number = scrapy.Field()
    origin = scrapy.Field()
    destination = scrapy.Field()
    pieces = scrapy.Field()
    weight = scrapy.Field()
    atd = scrapy.Field()
    ata = scrapy.Field()
