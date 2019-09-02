# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BaseVesselItem(scrapy.Item):
    pass


class VesselErrorData(BaseVesselItem):
    status = scrapy.Field()
    detail = scrapy.Field()
