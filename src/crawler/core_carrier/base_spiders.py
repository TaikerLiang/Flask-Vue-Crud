import scrapy

from .middlewares import CarrierSpiderMiddleware
from .pipelines import CarrierItemPipeline


CARRIER_CUSTOM_SETTINGS = {
    'SPIDER_MIDDLEWARES': {
        CarrierSpiderMiddleware.get_setting_name(): 900,
    },
    'ITEM_PIPELINES': {
        CarrierItemPipeline.get_setting_name(): 900,
    },
}

DISABLE_DUPLICATE_REQUEST_FILTER = {
    'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter'
}


class BaseCarrierSpider(scrapy.Spider):

    custom_settings = CARRIER_CUSTOM_SETTINGS

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs
        self.mbl_no = kwargs['mbl_no']

        self._error = False

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
