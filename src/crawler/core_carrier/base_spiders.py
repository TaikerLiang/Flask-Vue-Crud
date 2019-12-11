from pathlib import Path

import scrapy

from .middlewares import CarrierSpiderMiddleware
from .pipelines import CarrierItemPipeline
from ..general.savers import BaseSaver, FileSaver, NullSaver

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
        self.container_no = kwargs.get('container_no')

        to_save = ('save' in kwargs)
        self._saver = self._prepare_saver(to_save=to_save)

        self._error = False

    def _prepare_saver(self, to_save: bool) -> BaseSaver:
        if not to_save:
            return NullSaver()

        save_folder = Path(__file__).parent.parent.parent.parent / '_save_pages' / f'[{self.name}] {self.mbl_no}'

        return FileSaver(folder_path=save_folder, logger=self.logger)

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
