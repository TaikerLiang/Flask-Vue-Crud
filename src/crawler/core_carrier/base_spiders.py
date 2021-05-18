import abc
from pathlib import Path

import scrapy

from crawler.core_carrier.request_helpers import RequestOption
from .middlewares import CarrierSpiderMiddleware
from .pipelines import CarrierItemPipeline
from ..general.savers import BaseSaver, FileSaver, NullSaver
from ..utils.local_files.local_file_helpers import build_local_file_uri, LOCAL_PING_HTML


CARRIER_DEFAULT_SPIDER_MIDDLEWARES = {
    CarrierSpiderMiddleware.get_setting_name(): 900,
}


CARRIER_DEFAULT_ITEM_PIPELINES = {
    CarrierItemPipeline.get_setting_name(): 900,
}

CARRIER_DEFAULT_SETTINGS = {
    'SPIDER_MIDDLEWARES': {
        **CARRIER_DEFAULT_SPIDER_MIDDLEWARES,
    },
    'ITEM_PIPELINES': {
        **CARRIER_DEFAULT_ITEM_PIPELINES,
    },
}

DISABLE_DUPLICATE_REQUEST_FILTER = {'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter'}


class BaseCarrierSpider(scrapy.Spider):

    custom_settings = CARRIER_DEFAULT_SETTINGS

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs

        self.booking_no = kwargs.get('booking_no', '')
        self.mbl_no = kwargs.get('mbl_no', '')
        self.container_no_list = kwargs.get('container_no_list', '').split(',')

        to_save = 'save' in kwargs
        self._saver = self._prepare_saver(to_save=to_save)

        self._error = False

    def start_requests(self):
        url = build_local_file_uri(local_file=LOCAL_PING_HTML)
        yield scrapy.Request(url=url, callback=self._parse_start)

    def _parse_start(self, response):
        for r in self.start():
            yield r

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def _build_request_by(self, option: RequestOption):
        pass

    def _prepare_saver(self, to_save: bool) -> BaseSaver:
        if not to_save:
            return NullSaver()

        save_folder = (
                Path(__file__).parent.parent.parent.parent / '_save_pages' / f'[{self.name}] '
                f'{self.mbl_no or self.booking_no}'
        )

        return FileSaver(folder_path=save_folder, logger=self.logger)

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
