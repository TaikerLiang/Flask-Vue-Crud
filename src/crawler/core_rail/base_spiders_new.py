import abc
from pathlib import Path

import scrapy

from crawler.core.base_new import CLOSESPIDER_TIMEOUT, SEARCH_TYPE_CONTAINER
from crawler.core_rail.middlewares_new import RailSpiderMiddleware
from crawler.core_rail.pipelines_new import RailItemPipeline, RailMultiItemsPipeline
from crawler.core_rail.request_helpers_new import RequestOption
from crawler.general.savers import FileSaver, NullSaver
from crawler.utils.local_files.local_file_helpers import (
    LOCAL_PING_HTML,
    build_local_file_uri,
)

RAIL_DEFAULT_SPIDER_MIDDLEWARES = {
    RailSpiderMiddleware.get_setting_name(): 900,
}

RAIL_DEFAULT_ITEM_PIPELINES = {
    RailItemPipeline.get_setting_name(): 900,
}

RAIL_DEFAULT_SETTINGS = {
    "SPIDER_MIDDLEWARES": {
        **RAIL_DEFAULT_SPIDER_MIDDLEWARES,
    },
    "ITEM_PIPELINES": {
        **RAIL_DEFAULT_ITEM_PIPELINES,
    },
}


class BaseRailSpider(scrapy.Spider):

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": CLOSESPIDER_TIMEOUT,
        **RAIL_DEFAULT_SETTINGS,
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs

        self.container_no = kwargs["container_no"]

        self.search_type = SEARCH_TYPE_CONTAINER

        to_save = "save" in kwargs
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

        save_folder = Path(__file__).parent.parent.parent.parent / "_save_pages" / f"[{self.name}] {self.container_no}"

        return FileSaver(folder_path=save_folder, logger=self.logger)

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True


# ---------------------------------------------------------------------------------------------------------------------


RAIL_MULTI_ITEM_PIPELINES = {
    RailMultiItemsPipeline.get_setting_name(): 900,
}


class BaseMultiRailSpider(scrapy.Spider):

    custom_settings = {
        "CLOSESPIDER_TIMEOUT": CLOSESPIDER_TIMEOUT,
        "SPIDER_MIDDLEWARES": {
            **RAIL_DEFAULT_SPIDER_MIDDLEWARES,
        },
        "ITEM_PIPELINES": {
            **RAIL_MULTI_ITEM_PIPELINES,
        },
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)

        self.request_args = kwargs

        self.task_ids = [task_id.strip() for task_id in kwargs["task_ids"].split(",")]
        self.container_nos = [container_no.strip() for container_no in kwargs["container_nos"].split(",")]
        self.cno_tid_map = {}  # container_no: [task_ids]
        for c_no, t_id in zip(self.container_nos, self.task_ids):
            self.cno_tid_map.setdefault(c_no, [])
            self.cno_tid_map[c_no].append(t_id)

        self.search_type = SEARCH_TYPE_CONTAINER

        to_save = "save" in kwargs
        self._saver = self._prepare_saver(to_save=to_save)

        self._error = False

    def start_requests(self):
        # main entry point of scrapy
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

        save_folder = Path(__file__).parent.parent.parent.parent / "_save_pages" / f"[{self.name}] {self.container_nos}"

        return FileSaver(folder_path=save_folder, logger=self.logger)

    def has_error(self):
        return self._error

    def mark_error(self):
        self._error = True
