import scrapy


class BaseItem(scrapy.Item):
    pass


class ExportErrorData(BaseItem):
    task_id = scrapy.Field()
    mbl_no = scrapy.Field()
    mawb_no = scrapy.Field()
    booking_no = scrapy.Field()
    container_no = scrapy.Field()
    type = scrapy.Field()  # carrier/terminal/rail/air
    status = scrapy.Field()
    detail = scrapy.Field()
    traceback_info = scrapy.Field()
