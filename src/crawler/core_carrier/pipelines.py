import pprint
import os
import traceback
from collections import OrderedDict
from typing import Dict

from scrapy.exceptions import DropItem

from . import items as carrier_items
from .base import CARRIER_RESULT_STATUS_DATA, CARRIER_RESULT_STATUS_DEBUG, CARRIER_RESULT_STATUS_FATAL, SHIPMENT_TYPE_BOOKING, SHIPMENT_TYPE_MBL
from crawler.services.edi_service import EdiClientService


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


class CarrierMultiItemsPipeline:
    def __init__(self):
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f'{__name__}.{cls.__name__}'

    def open_spider(self, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- open_spider -----')
        for task_id, search_no in zip(spider.task_ids, spider.search_nos):
            request_args = {
                'task_id': task_id,
                'save': spider.request_args.get('save'),
            }

            if spider.search_type == SHIPMENT_TYPE_MBL:
                request_args.update({'mbl_no': search_no})
            elif spider.search_type == SHIPMENT_TYPE_BOOKING:
                request_args.update({'booking_no': search_no})

            self._collector_map.setdefault(task_id, CarrierResultCollector(request_args=request_args))

    def process_item(self, item, spider):
        spider.logger.info(f'[{self.__class__.__name__}] ----- process_item -----')
        spider.logger.info(f'item : {pprint.pformat(item)}')

        default_collector = CarrierResultCollector(request_args=spider.request_args)
        try:
            collector = self._collector_map[item['task_id']] if 'task_id' in item else default_collector

            if isinstance(item, carrier_items.MblItem):
                collector.collect_mbl_item(item=item)
            elif isinstance(item, carrier_items.VesselItem):
                collector.collect_vessel_item(item=item)
            elif isinstance(item, carrier_items.ContainerItem):
                collector.collect_container_item(item=item)
            elif isinstance(item, carrier_items.ContainerStatusItem):
                collector.collect_container_status_item(item=item)
            elif isinstance(item, carrier_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {'status': 'CLOSE', 'result': res}
            elif isinstance(item, carrier_items.ExportErrorData):
                results = default_collector.build_error_data(item)
                collector_results = self._get_results_of_collectors()
                results = [results] + collector_results if collector_results else results
                return {'results': results}
            elif isinstance(item, carrier_items.DebugItem):
                debug_data = default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f'unknown item: {item}')
        except:
            spider.mark_error()
            status = CARRIER_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = carrier_items.ExportErrorData(status=status, detail=detail)
            results = default_collector.build_error_data(err_item)
            collector_results = self._get_results_of_collectors()
            results = [results] + collector_results if collector_results else results
            return results

        raise DropItem('item processed')

    def _get_results_of_collectors(self):
        results = []
        for _, collector in self._collector_map.items():
            results.append(collector.build_final_data())

        return results

    def _send_result_back_to_edi_engine(self):
        user = os.environ.get('EDI_ENGINE_USER')
        token = os.environ.get('EDI_ENGINE_TOKEN')
        edi_client = EdiClientService(edi_user=user, edi_token=token)

        res = []
        for task_id, collector in self._collector_map.items():
            item_result = collector.build_final_data()
            status_code, text = edi_client.send_provider_result_back(task_id=task_id, provider_code='scrapy_cloud_api', item_result=item_result)
            res.append({'task_id': task_id, 'status_code': status_code, 'text': text})

        return res


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
        # remove task_id, task_id is just for link different items in same task
        if 'task_id' in self._basic:
            del self._basic['task_id']

        vessels = []
        for vessel in list(self._vessels.values()):
            if 'task_id' in vessel:
                del vessel['task_id']
            vessels.append(vessel)

        containers = []
        for container in list(self._containers.values()):
            for status in container['status']:
                if 'task_id' in status:
                    del status['task_id']
            containers.append(container)

        return {
            'status': CARRIER_RESULT_STATUS_DATA,
            'request_args': self._request_args,
            'basic': self._basic,
            'vessels': vessels,
            'containers': containers,
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
        res = {}
        for k, v in item.items():
            if k.startswith('_'):
                continue
            if isinstance(v, carrier_items.LocationItem):
                res.update({k: dict(v)})
            else:
                res.update({k: v})

        return res
