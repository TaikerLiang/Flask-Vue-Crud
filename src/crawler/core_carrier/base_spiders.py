import scrapy

from .middlewares import CarrierSpiderMiddleware
from .pipelines import CarrierItemPipeline


class BaseCarrierSpider(scrapy.Spider):

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            CarrierSpiderMiddleware.get_setting_name(): 900,
        },
        'ITEM_PIPELINES': {
            CarrierItemPipeline.get_setting_name(): 900,
        },
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs
        self.mbl_no = kwargs['mbl_no']

        self._error = False

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
