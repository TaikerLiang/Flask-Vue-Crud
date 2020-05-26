# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BaseVesselItem(scrapy.Item):
    pass


class DebugItem(BaseVesselItem):
    info = scrapy.Field()


class VesselPortItem(BaseVesselItem):
    etd = scrapy.Field()
    atd = scrapy.Field()
    eta = scrapy.Field()
    ata = scrapy.Field()
    name = scrapy.Field()
    un_lo_code = scrapy.Field()


class VesselErrorData(BaseVesselItem):
    status = scrapy.Field()
    detail = scrapy.Field()
