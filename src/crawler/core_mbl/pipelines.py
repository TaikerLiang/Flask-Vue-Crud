# -*- coding: utf-8 -*-
import pprint
from collections import defaultdict

from scrapy.exceptions import DropItem

from crawler.core_mbl import items as mbl_items


class MblItemPipeline(object):

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')

        self._request_args = spider.request_args
        self._basic = {}
        self._vessels = defaultdict(dict)
        self._containers = defaultdict(dict)

    def _create_final_data(self):
        return {
            'status': 'OK',
            'request_args': dict(self._request_args),
            'basic': dict(self._basic),
            'vessels': dict(self._vessels),
            'containers': dict(self._containers),
        }

    def _create_error_data(self, item):
        return {
            'status': 'ERROR',
            'request_args': dict(self._request_args),
            'error': dict(item),
        }

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        # drop private keys (startswith '_')
        clean_item = {
            k: v
            for k, v in item.items()
            if not k.startswith('_')
        }

        if isinstance(item, mbl_items.MblItem):
            self._basic.update(clean_item)
        elif isinstance(item, mbl_items.VesselItem):
            self._vessels[item.key].update(clean_item)
        elif isinstance(item, mbl_items.ContainerStatusItem):
            self._containers[item.key].update(clean_item)
        elif isinstance(item, mbl_items.ExportFinalData):
            return self._create_final_data()
        elif isinstance(item, mbl_items.ExportErrorData):
            return self._create_error_data(clean_item)
        else:
            raise DropItem(f'unknown item: {item}')

        raise DropItem('item processed')
