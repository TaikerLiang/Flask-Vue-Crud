import scrapy


class BaseRailItem(scrapy.Item):
    pass


class ExportFinalData(BaseRailItem):
    pass


class ExportErrorData(BaseRailItem):
    status = scrapy.Field()
    detail = scrapy.Field()
    traceback_info = scrapy.Field()


class RailItem(BaseRailItem):
    task_id = scrapy.Field()
    container_no = scrapy.Field()

    # CP
    status = scrapy.Field()
    grounded = scrapy.Field()
    last_event = scrapy.Field()
    lfd = scrapy.Field()
    hold = scrapy.Field()

    # NS
    last_event_date = scrapy.Field()
    # last_event_code
    origin_location = scrapy.Field()
    final_destination = scrapy.Field()

    # Share
    current_location = scrapy.Field()
    eta = scrapy.Field()
    ata = scrapy.Field()

    @property
    def key(self):
        return self['task_id']


class DebugItem(BaseRailItem):
    info = scrapy.Field()


class InvalidContainerNoItem(BaseRailItem):
    task_id = scrapy.Field()
    container_no = scrapy.Field()

