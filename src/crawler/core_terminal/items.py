import scrapy


class BaseTerminalItem(scrapy.Item):
    pass


class ExportFinalData(BaseTerminalItem):
    pass


class ExportErrorData(BaseTerminalItem):
    status = scrapy.Field()
    detail = scrapy.Field()
    traceback_info = scrapy.Field()


class TerminalItem(BaseTerminalItem):
    container_no = scrapy.Field()
    freight_release = scrapy.Field()
    customs_release = scrapy.Field()
    discharge_date = scrapy.Field()
    ready_for_pick_up = scrapy.Field()
    appointment_date = scrapy.Field()
    last_free_day = scrapy.Field()
    gate_out_date = scrapy.Field()
    demurrage = scrapy.Field()
    carrier = scrapy.Field()
    container_spec = scrapy.Field()
    holds = scrapy.Field()
    cy_location = scrapy.Field()  # location ?
    vessel = scrapy.Field()
    mbl_no = scrapy.Field()
    voyage = scrapy.Field()
    weight = scrapy.Field()
    hazardous = scrapy.Field()
    chassis_no = scrapy.Field()

    @property
    def key(self):
        return self.container_no


class DebugItem(BaseTerminalItem):
    info = scrapy.Field()

