import pprint
import traceback
from typing import Dict

from scrapy.exceptions import DropItem

from . import items as terminal_items
from .base import TERMINAL_RESULT_STATUS_DATA, TERMINAL_RESULT_STATUS_FATAL, TERMINAL_RESULT_STATUS_DEBUG


class TerminalItemPipeline:

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._collector = TerminalResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, terminal_items.TerminalItem):
                self._collector.collect_terminal_item(item=item)
            elif isinstance(item, terminal_items.ExportFinalData):
                return self._collector.build_final_data()
            elif isinstance(item, terminal_items.ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, terminal_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f'unknown item: {item}')

        except:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
            return self._collector.build_error_data(err_item)

        raise DropItem('item processed')


class TerminalMultiItemsPipeline:

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._collector_map = {}
        for container_no in spider.container_no_list:
            self._collector_map.setdefault(container_no, TerminalResultCollector(request_args=spider.request_args))

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, terminal_items.TerminalItem):
                collector item.key
                self._collector.collect_terminal_item(item=item)
            elif isinstance(item, terminal_items.ExportFinalData):
                return self._collector.build_final_data()
            elif isinstance(item, terminal_items.ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, terminal_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f'unknown item: {item}')

        except:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
            return self._collector.build_error_data(err_item)

        raise DropItem('item processed')

class TerminalResultCollector:

    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._terminal = {}

    def collect_terminal_item(self, item: terminal_items.TerminalItem):
        clean_dict = self._clean_item(item)
        self._terminal.update(clean_dict)

    def build_final_data(self) -> Dict:
        return {
            'status': TERMINAL_RESULT_STATUS_DATA,
            'request_args': self._request_args,
            'terminal': self._terminal,
        }

    def build_error_data(self, item: terminal_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': TERMINAL_RESULT_STATUS_FATAL,  # default status
            'request_args': self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: terminal_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': TERMINAL_RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {
            k: v
            for k, v in item.items()
            if not k.startswith('_')
        }