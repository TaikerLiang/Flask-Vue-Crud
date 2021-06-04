import pprint
import traceback
from typing import Dict

from scrapy.exceptions import DropItem

from . import items as rail_items
from .base import RAIL_RESULT_STATUS_DATA, RAIL_RESULT_STATUS_FATAL, RAIL_RESULT_STATUS_DEBUG, RAIL_RESULT_STATUS_ERROR


class RailItemPipeline:
    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._collector = RailResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, rail_items.RailItem):
                self._collector.collect_terminal_item(item=item)
            elif isinstance(item, rail_items.ExportFinalData):
                return self._collector.build_final_data()
            elif isinstance(item, rail_items.ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, rail_items.DebugItem):
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


class RailMultiItemsPipeline:
    def __init__(self):
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._default_collector = RailResultCollector(request_args=spider.request_args)
        for task_id, container_no in zip(spider.task_ids, spider.container_nos):
            self._collector_map.setdefault(
                task_id,
                RailResultCollector(
                    request_args={
                        'task_id': task_id,
                        'container_no': container_no,
                        'save': spider.request_args.get('save'),
                    }
                ),
            )

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, rail_items.RailItem):
                collector = self._collector_map[item.key] if item.key else self._default_collector
                collector.collect_terminal_item(item=item)
                return collector.build_final_data()
            elif isinstance(item, rail_items.InvalidContainerNoItem):
                return self._default_collector.build_invalid_no_data(item=item)
            elif isinstance(item, rail_items.ExportFinalData):
                return {'status': 'CLOSE'}
            elif isinstance(item, rail_items.ExportErrorData):
                results = self._default_collector.build_error_data(item)
                collector_results = self._get_results_of_collectors()
                results = [results] + collector_results if collector_results else results
                return {'results': results}
            elif isinstance(item, rail_items.DebugItem):
                debug_data = self._default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f'unknown item: {item}')

        except:
            spider.mark_error()
            status = RAIL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = rail_items.ExportErrorData(status=status, detail=detail)

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


class RailResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._rail = {}

    def collect_terminal_item(self, item: rail_items.RailItem):
        clean_dict = self._clean_item(item)
        self._rail.update(clean_dict)
        # return self._terminal

    def build_final_data(self) -> Dict:
        return {
            'status': RAIL_RESULT_STATUS_DATA,
            'request_args': self._request_args,
            'rail': self._rail,
        }

    def build_error_data(self, item: rail_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': RAIL_RESULT_STATUS_FATAL,  # default status
            'request_args': self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: rail_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': RAIL_RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    def build_invalid_no_data(self, item: rail_items.InvalidContainerNoItem) -> Dict:

        return {
            'status': RAIL_RESULT_STATUS_ERROR,  # default status
            'request_args': self._request_args,
            'invalid_container_no': item['container_no'],
            'task_id': item['task_id'],
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {k: v for k, v in item.items() if not k.startswith('_')}

    def is_item_empty(self) -> bool:
        return not bool(self._rail)
