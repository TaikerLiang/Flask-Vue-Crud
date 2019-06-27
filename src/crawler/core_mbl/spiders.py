# -*- coding: utf-8 -*-
import scrapy

from crawler.core_mbl.middlewares import MblSpiderMiddleware
from crawler.core_mbl.pipelines import MblItemPipeline


class MblSpiderBase(scrapy.Spider):

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            MblSpiderMiddleware.get_setting_name(): 900,
        },
        'ITEM_PIPELINES': {
            MblItemPipeline.get_setting_name(): 900,
        },
    }

    def __init__(self, name=None, **kwargs):
        super(MblSpiderBase, self).__init__(name=name, **kwargs)

        self.request_args = kwargs
        self.mbl_no = kwargs['mbl_no']

        self._error = False

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
