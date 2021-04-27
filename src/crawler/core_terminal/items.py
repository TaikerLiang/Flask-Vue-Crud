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
    task_id = scrapy.Field()
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

    # tti field
    demurrage_due = scrapy.Field()
    pay_through_date = scrapy.Field()

    # ets field
    service = scrapy.Field()
    carrier_release = scrapy.Field()
    demurrage_status = scrapy.Field()

    # tti & ets field
    tmf = scrapy.Field()

    # lbct field
    owed = scrapy.Field()
    full_empty = scrapy.Field()

    @property
    def key(self):
        return self['task_id']


class DebugItem(BaseTerminalItem):
    info = scrapy.Field()


class InvalidContainerNoItem(BaseTerminalItem):
    task_id = scrapy.Field()
    container_no = scrapy.Field()

