import scrapy

from crawler.core_vessel.middlewares import VesselSpiderMiddleware
from crawler.core_vessel.pipelines import VesselItemPipeline


class BaseVesselSpider(scrapy.Spider):

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            VesselSpiderMiddleware.get_setting_name(): 900,
        },
        'ITEM_PIPELINES': {
            VesselItemPipeline.get_setting_name(): 900,
        }
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs

        self._error = False

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
