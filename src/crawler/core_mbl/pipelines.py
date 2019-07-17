# -*- coding: utf-8 -*-
import pprint
from collections import defaultdict
from typing import Dict

from scrapy.exceptions import DropItem

from crawler.core_mbl import items as mbl_items


class MblItemPipeline(object):

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._collector = _MblResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        if isinstance(item, mbl_items.MblItem):
            self._collector.collect_mbl_item(item=item)
        elif isinstance(item, mbl_items.VesselItem):
            self._collector.collect_vessel_item(item=item)
        elif isinstance(item, mbl_items.ContainerItem):
            self._collector.collect_container_item(item=item)
        elif isinstance(item, mbl_items.ContainerStatusItem):
            self._collector.collect_container_status_item(item=item)
        elif isinstance(item, mbl_items.ExportFinalData):
            return self._collector.build_final_data()
        elif isinstance(item, mbl_items.ExportErrorData):
            return self._collector.build_error_data(item)
        else:
            raise DropItem(f'unknown item: {item}')

        raise DropItem('item processed')


class _MblResultCollector:

    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._basic = {}
        self._vessels = defaultdict(dict)
        self._containers = {}

    def collect_mbl_item(self, item: mbl_items.MblItem):
        clean_dict = self._clean_item(item)
        self._basic.update(clean_dict)

    def collect_vessel_item(self, item: mbl_items.VesselItem):
        clean_dict = self._clean_item(item)
        self._vessels[item.key].update(clean_dict)

    def collect_container_item(self, item: mbl_items.ContainerItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._containers:
            self._containers[item.key] = self._get_default_container_data(container_no=item['container_no'])

        self._containers[item.key].update(clean_dict)

    def collect_container_status_item(self, item: mbl_items.ContainerStatusItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._containers:
            self._containers[item.key] = self._get_default_container_data(container_no=item['container_no'])

        self._containers[item.key]['status'].append(clean_dict)

    @staticmethod
    def _get_default_container_data(container_no: str):
        return {
            'container_no': container_no,
            'status': [],
        }

    def build_final_data(self) -> Dict:
        return {
            'status': 'OK',
            'request_args': self._request_args,
            'basic': self._basic,
            'vessels': dict(self._vessels),
            'containers': self._containers,
        }

    def build_error_data(self, item: mbl_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)
        return {
            'status': 'ERROR',
            'request_args': self._request_args,
            'error': clean_dict,
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
