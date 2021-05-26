import abc
from pathlib import Path

import scrapy

from crawler.core_vessel.middlewares import VesselSpiderMiddleware
from crawler.core_vessel.pipelines import VesselItemPipeline
from crawler.core_vessel.request_helpers import RequestOption
from crawler.general.savers import NullSaver, FileSaver
from crawler.utils.local_files.local_file_helpers import build_local_file_uri, LOCAL_PING_HTML


class BaseVesselSpider(scrapy.Spider):

    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            VesselSpiderMiddleware.get_setting_name(): 900,
        },
        'ITEM_PIPELINES': {
            VesselItemPipeline.get_setting_name(): 900,
        },
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.scac = kwargs['scac']
        self.vessel_name = kwargs['vessel_name']
        self.request_args = kwargs

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

    def _prepare_saver(self, to_save: bool):
        if not to_save:
            return NullSaver()

        save_folder = (
            Path(__file__).parent.parent.parent.parent / '_save_pages' / f'[{self.name}] {self.scac} {self.vessel_name}'
        )

        return FileSaver(folder_path=save_folder, logger=self.logger)

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
