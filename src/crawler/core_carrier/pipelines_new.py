from collections import OrderedDict
import pprint
import traceback
from typing import Dict, Optional

from scrapy.exceptions import DropItem

from crawler.core.base_new import (
    RESULT_STATUS_DATA,
    RESULT_STATUS_DEBUG,
    RESULT_STATUS_FATAL,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_MBL,
)
from crawler.core.exceptions_new import DidNotEndError
from crawler.core.items_new import DataNotFoundItem, EndItem, ExportErrorData
from crawler.core.pipelines import BaseItemPipeline
from crawler.core_carrier import items_new as carrier_items


class CarrierItemPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-carrier/local/")

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        self._collector = CarrierResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        try:
            if isinstance(item, carrier_items.MblItem):
                self._collector.collect_mbl_item(item=item)
            elif isinstance(item, carrier_items.VesselItem):
                self._collector.collect_vessel_item(item=item)
            elif isinstance(item, carrier_items.ContainerItem):
                self._collector.collect_container_item(item=item)
            elif isinstance(item, carrier_items.ContainerStatusItem):
                self._collector.collect_container_status_item(item=item)
            elif isinstance(item, carrier_items.RailItem):
                self._collector.collect_rail_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                self._collector.collect_not_found_item(item=item)
            elif isinstance(item, EndItem):
                self._collector.set_is_end()
            # TODO All kinds of ExportFinalData should be migrate to core/items.py
            elif isinstance(item, carrier_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine(spider=spider)
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, ExportErrorData):
                self._collector.collect_error_item(item=item)
            elif isinstance(item, carrier_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f"unknown item: {item}")

        except Exception:
            spider.mark_error()
            status = RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = ExportErrorData(status=status, detail=detail)
            result = self._collector.build_error_data(err_item)

            res = self._send_error_msg_back_to_edi_engine(result=result)
            return {"status": "CLOSE", "result": res}

        raise DropItem("item processed")

    def _send_result_back_to_edi_engine(self, spider):
        res = []
        if self._collector.has_error():
            item_result = self._collector.get_error_item()
        elif self._collector.has_not_found():
            item_result = self._collector.get_not_found_item()
        elif not self._collector.is_end():
            item_result = dict(DidNotEndError(task_id=spider.task_id).build_error_data())
        else:
            item_result = self._collector.build_final_data()

        task_id = item_result.get("request_args", {}).get("task_id")
        if task_id:
            status_code, text = self.send_provider_result_to_edi_client(task_id=task_id, item_result=item_result)
            res.append({"task_id": task_id, "status_code": status_code, "text": text, "data": item_result})
            return res
        else:
            return {"status_code": -1, "text": "no task id in request_args or empty result"}

    def _send_error_msg_back_to_edi_engine(self, result: Dict):
        res = []
        task_id = result.get("request_args", {}).get("task_id")
        status_code, text = self.handle_err_result(collector=self._collector, task_id=task_id, result=result)
        res.append({"task_id": task_id, "status_code": status_code, "text": text})
        return res


class CarrierMultiItemsPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-carrier/local/")
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")
        for task_id, search_no in zip(spider.task_ids, spider.search_nos):
            request_args = {
                "task_id": task_id,
                "save": spider.request_args.get("save"),
            }

            if spider.search_type == SEARCH_TYPE_MBL:
                request_args.update({"mbl_no": search_no})
            elif spider.search_type == SEARCH_TYPE_BOOKING:
                request_args.update({"booking_no": search_no})

            self._collector_map.setdefault(task_id, CarrierResultCollector(request_args=request_args))

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        default_collector = CarrierResultCollector(request_args=spider.request_args)
        try:
            collector = self._collector_map[item["task_id"]] if "task_id" in item else default_collector

            if isinstance(item, carrier_items.MblItem):
                collector.collect_mbl_item(item=item)
            elif isinstance(item, carrier_items.VesselItem):
                collector.collect_vessel_item(item=item)
            elif isinstance(item, carrier_items.ContainerItem):
                collector.collect_container_item(item=item)
            elif isinstance(item, carrier_items.ContainerStatusItem):
                collector.collect_container_status_item(item=item)
            elif isinstance(item, carrier_items.RailItem):
                collector.collect_rail_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                collector.collect_not_found_item(item=item)
            elif isinstance(item, ExportErrorData):
                collector.collect_error_item(item=item)
            elif isinstance(item, EndItem):
                collector.set_is_end()
            # TODO All kinds of ExportFinalData should be migrate to core/items.py
            elif isinstance(item, carrier_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, carrier_items.DebugItem):
                debug_data = default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f"unknown item: {item}")
        except Exception:
            spider.mark_error()
            status = RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = ExportErrorData(status=status, detail=detail)
            result = default_collector.build_error_data(err_item)

            res = self._send_error_msg_back_to_edi_engine(result=result)
            return {"status": "CLOSE", "result": res}

        raise DropItem("item processed")

    def _send_result_back_to_edi_engine(self):
        res = []
        for task_id, collector in self._collector_map.items():
            if collector.has_error():
                item_result = collector.get_error_item()
            elif collector.has_not_found():
                item_result = collector.get_not_found_item()
            elif not collector.is_end():
                item_result = dict(DidNotEndError(task_id=task_id).build_error_data())
            else:
                item_result = collector.build_final_data()

            if item_result:
                status_code, text = self.send_provider_result_to_edi_client(task_id=task_id, item_result=item_result)
                res.append({"task_id": task_id, "status_code": status_code, "text": text, "data": item_result})

        return res

    def _send_error_msg_back_to_edi_engine(self, result: Dict):
        res = []
        for task_id, collector in self._collector_map.items():
            status_code, text = self.handle_err_result(collector=collector, task_id=task_id, result=result)
            res.append({"task_id": task_id, "status_code": status_code, "text": text})

        return res


class CarrierResultCollector:
    def __init__(self, request_args):
        self._is_end = False
        self._request_args = dict(request_args)
        self._error = {}
        self._not_found = {}
        self._basic = {}
        self._vessels = OrderedDict()
        self._containers = OrderedDict()
        self._rails = OrderedDict()

    def collect_error_item(self, item: ExportErrorData):
        clean_dict = self._clean_item(item)
        self._error.update(clean_dict)

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

        self._containers[item.key]["status"].append(clean_dict)

    def collect_rail_item(self, item: carrier_items.RailItem):
        clean_dict = self._clean_item(item)

        if item.key not in self._rails:
            self._containers[item.key] = self._get_default_container_data(container_key=item.key)

        self._containers[item.key]["rail_status"].append(clean_dict)

    def collect_not_found_item(self, item: DataNotFoundItem):
        clean_dict = self._clean_item(item)
        self._not_found.update(clean_dict)

    @staticmethod
    def _get_default_vessel_data(vessel_key: str):
        return {
            "vessel_key": vessel_key,
        }

    @staticmethod
    def _get_default_container_data(container_key: str):
        return {
            "container_key": container_key,
            "container_no": container_key,
            "status": [],
            "rail_status": [],
        }

    def build_final_data(self) -> Optional[Dict]:
        # remove task_id, task_id is just for link different items in same task
        if "task_id" in self._basic:
            del self._basic["task_id"]

        vessels = []
        for vessel in list(self._vessels.values()):
            if "task_id" in vessel:
                del vessel["task_id"]
            vessels.append(vessel)

        containers = []
        for container in list(self._containers.values()):
            new_status = []
            new_rail_status = []

            # remove duplicated status
            for idx, status in enumerate(container["status"]):
                if status in container["status"][idx + 1 :]:
                    continue
                if "task_id" in status:
                    del status["task_id"]
                new_status.append(status)

            # remove duplicated rail status
            for idx, rail_status in enumerate(container["rail_status"]):
                if rail_status in container["rail_status"][idx + 1 :]:
                    continue
                if "task_id" in rail_status:
                    del rail_status["task_id"]
                new_rail_status.append(rail_status)

            container["status"] = new_status
            container["rail_status"] = new_rail_status
            containers.append(container)

        if self._basic or vessels or containers:
            return {
                "status": RESULT_STATUS_DATA,
                "request_args": self._request_args,
                "basic": self._basic,
                "vessels": vessels,
                "containers": containers,
            }

    def build_error_data(self, item: ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": RESULT_STATUS_FATAL,  # default status
            "request_args": self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: carrier_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        res = {}
        for k, v in item.items():
            if k.startswith("_"):
                continue
            if isinstance(v, carrier_items.LocationItem):
                res.update({k: dict(v)})
            else:
                res.update({k: v})

        return res

    def set_is_end(self):
        self._is_end = True

    def is_end(self):
        return self._is_end

    def is_default(self):
        return False if self._basic else True

    def has_error(self):
        return True if self._error else False

    def has_not_found(self):
        return True if self._not_found else False

    def get_error_item(self):
        self._error.update({"request_args": self._request_args})
        return self._error

    def get_not_found_item(self):
        self._not_found.update({"request_args": self._request_args})
        return self._not_found