import pprint
import traceback
from typing import Dict

from scrapy.exceptions import DropItem

from . import items as terminal_items
from .base import TERMINAL_RESULT_STATUS_DATA, TERMINAL_RESULT_STATUS_FATAL, TERMINAL_RESULT_STATUS_DEBUG, \
    TERMINAL_RESULT_STATUS_ERROR


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


# ---------------------------------------------------------------------------------------------------------------------


class TerminalMultiItemsPipeline:

    def __init__(self):
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._default_collector = TerminalResultCollector(request_args=spider.request_args)
        for task_id, container_no in zip(spider.task_ids, spider.container_nos):
            self._collector_map.setdefault(task_id, TerminalResultCollector(request_args={
                'task_id': task_id,
                'container_no': container_no,
                'save': spider.request_args.get('save'),
            }))

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, terminal_items.TerminalItem):
                collector = self._collector_map[item.key] if item.key else self._default_collector
                collector.collect_terminal_item(item=item)
            elif isinstance(item, terminal_items.InvalidContainerNoItem):
                return self._default_collector.build_invalid_no_data(item=item)
            elif isinstance(item, terminal_items.ExportFinalData):
                results = self._get_results_of_collectors()
                return {'results': results}
            elif isinstance(item, terminal_items.ExportErrorData):
                results = self._default_collector.build_error_data(item)
                collector_results = self._get_results_of_collectors()
                results = [results] + collector_results if collector_results else results
                return {'results': results}
            elif isinstance(item, terminal_items.DebugItem):
                debug_data = self._default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f'unknown item: {item}')

        except:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)

            results = self._default_collector.build_error_data(err_item)
            collector_results = self._get_results_of_collectors()
            results = [results] + collector_results if collector_results else results
            return results

        raise DropItem('item processed')

    def _get_results_of_collectors(self):
        results = []
        for container_no, collector in self._collector_map.items():
            if not collector.is_item_empty():
                results.append(collector.build_final_data())

        return results


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

    def build_invalid_no_data(self, item: terminal_items.InvalidContainerNoItem) -> Dict:

        return {
            'status': TERMINAL_RESULT_STATUS_ERROR,  # default status
            'request_args': self._request_args,
            'invalid_container_no': item['container_no'],
            'task_id': item['task_id'],
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

    def is_item_empty(self) -> bool:
        return not bool(self._terminal)

