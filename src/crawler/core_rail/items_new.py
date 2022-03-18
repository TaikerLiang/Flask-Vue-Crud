import scrapy


class BaseRailItem(scrapy.Item):
    pass


class ExportFinalData(BaseRailItem):
    pass


class RailItem(BaseRailItem):
    task_id = scrapy.Field()
    container_no = scrapy.Field()
    description = scrapy.Field()

    # CP
    last_event = scrapy.Field()
    load_status = scrapy.Field()
    grounded = scrapy.Field()
    last_event_location = scrapy.Field()
    hold = scrapy.Field()

    # NS
    last_event_date = scrapy.Field()
    origin_location = scrapy.Field()
    final_destination = scrapy.Field()
    final_dest_eta = scrapy.Field()

    # Share
    current_location = scrapy.Field()
    eta = scrapy.Field()
    ata = scrapy.Field()
    last_free_day = scrapy.Field()
    last_event_time = scrapy.Field()

    @property
    def key(self):
        return self["task_id"]


class DebugItem(BaseRailItem):
    info = scrapy.Field()


class InvalidItem(BaseRailItem):
    task_id = scrapy.Field()
    container_no = scrapy.Field()


class InvalidContainerNoItem(InvalidItem):
    pass
