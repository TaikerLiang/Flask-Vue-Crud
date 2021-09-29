import scrapy


class BaseAirItem(scrapy.Item):
    pass


class ExportFinalData(BaseAirItem):
    pass


class ExportErrorData(BaseAirItem):
    task_id = scrapy.Field()
    mawb_no = scrapy.Field()
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

    @property
    def key(self):
        return self["task_id"]


class FlightItem(BaseAirItem):
    task_id = scrapy.Field()
    flight_number = scrapy.Field()
    origin = scrapy.Field()
    destination = scrapy.Field()
    pieces = scrapy.Field()
    weight = scrapy.Field()
    atd = scrapy.Field()
    ata = scrapy.Field()

    @property
    def key(self):
        return self["task_id"]


class HistoryItem(BaseAirItem):
    task_id = scrapy.Field()
    status = scrapy.Field()
    pieces = scrapy.Field()
    weight = scrapy.Field()
    time = scrapy.Field()
    location = scrapy.Field()
    flight_no = scrapy.Field()

    @property
    def key(self):
        return self["task_id"]


class InvalidMawbNoItem(BaseAirItem):
    task_id = scrapy.Field()
    mawb = scrapy.Field()
