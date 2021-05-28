import pprint
import traceback
from collections import OrderedDict
from typing import Dict

from scrapy.exceptions import DropItem

from . import items as carrier_items
from .base import CARRIER_RESULT_STATUS_DATA, CARRIER_RESULT_STATUS_DEBUG, CARRIER_RESULT_STATUS_FATAL


class CarrierItemPipeline:
    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._collector = CarrierResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        try:
            if isinstance(item, carrier_items.MblItem):
                self._collector.collect_mbl_item(item=item)
            elif isinstance(item, carrier_items.VesselItem):
                self._collector.collect_vessel_item(item=item)
            elif isinstance(item, carrier_items.ContainerItem):
                self._collector.collect_container_item(item=item)
            elif isinstance(item, carrier_items.ContainerStatusItem):
                self._collector.collect_container_status_item(item=item)
            elif isinstance(item, carrier_items.ExportFinalData):
                return self._collector.build_final_data()
            elif isinstance(item, carrier_items.ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, carrier_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f'unknown item: {item}')

        except:
            spider.mark_error()
            status = CARRIER_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = carrier_items.ExportErrorData(status=status, detail=detail)
            return self._collector.build_error_data(err_item)

        raise DropItem('item processed')


class CarrierResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._basic = {}
        self._vessels = OrderedDict()
        self._containers = OrderedDict()

    def collect_mbl_item(self, item: carrier_items.MblItem):
        clean_dict = self._clean_item(item)
        self._basic.update(clean_dict)

    def collect_vessel_item(self, item: carrier_items.VesselItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._vessels:
            self._vessels[item.key] = self._get_default_vessel_data(vessel_key=item.key)

        self._vessels[item.key].update(clean_dict)

    def collect_container_item(self, item: carrier_items.ContainerItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._containers:
            self._containers[item.key] = self._get_default_container_data(container_key=item.key)

        self._containers[item.key].update(clean_dict)

    def collect_container_status_item(self, item: carrier_items.ContainerStatusItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._containers:
            self._containers[item.key] = self._get_default_container_data(container_key=item.key)

        self._containers[item.key]['status'].append(clean_dict)

    @staticmethod
    def _get_default_vessel_data(vessel_key: str):
        return {
            'vessel_key': vessel_key,
        }

    @staticmethod
    def _get_default_container_data(container_key: str):
        return {
            'container_key': container_key,
            'status': [],
        }

    def build_final_data(self) -> Dict:
        return {
            'status': CARRIER_RESULT_STATUS_DATA,
            'request_args': self._request_args,
            'basic': self._basic,
            'vessels': list(self._vessels.values()),
            'containers': list(self._containers.values()),
        }

    def build_error_data(self, item: carrier_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': CARRIER_RESULT_STATUS_FATAL,  # default status
            'request_args': self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: carrier_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            'status': CARRIER_RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {k: v for k, v in item.items() if not k.startswith('_')}
