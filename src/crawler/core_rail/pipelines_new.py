import pprint
import traceback
from typing import Dict, Optional

from scrapy.exceptions import DropItem

from crawler.core.base_new import (
    RESULT_STATUS_DATA,
    RESULT_STATUS_DEBUG,
    RESULT_STATUS_FATAL,
)
from crawler.core.items_new import DataNotFoundItem, ExportErrorData
from crawler.core.pipelines import BaseItemPipeline
from crawler.core_rail import items_new as rail_items


class RailItemPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-rail/local/")

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        self._collector = RailResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        try:
            if isinstance(item, rail_items.RailItem):
                self._collector.collect_rail_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                self._collector.collect_not_found_item(item=item)
            elif isinstance(item, rail_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, rail_items.DebugItem):
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

    def _send_result_back_to_edi_engine(self):
        res = []
        if self._collector.has_error():
            item_result = self._collector.get_error_item()
        elif self._collector.has_not_found():
            item_result = self._collector.get_not_found_item()
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


# ---------------------------------------------------------------------------------------------------------------------


class RailMultiItemsPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-rail/local/")
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        for task_id, container_no in zip(spider.task_ids, spider.container_nos):
            request_args = {
                "task_id": task_id,
                "container_no": container_no,
                "save": spider.request_args.get("save"),
            }

            self._collector_map.setdefault(task_id, RailResultCollector(request_args=request_args))

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        default_collector = RailResultCollector(request_args=spider.request_args)

        try:
            collector = self._collector_map[item["task_id"]] if "task_id" in item else default_collector

            if isinstance(item, rail_items.RailItem):
                collector.collect_rail_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                collector.collect_not_found_item(item=item)
            elif isinstance(item, rail_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, ExportErrorData):
                collector.collect_error_item(item=item)
            elif isinstance(item, rail_items.DebugItem):
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

    def _get_results_of_collectors(self):
        results = []
        for container_no, collector in self._collector_map.items():
            if not collector.is_item_empty():
                results.append(collector.build_final_data())

        return results

    def _send_result_back_to_edi_engine(self):
        res = []
        for task_id, collector in self._collector_map.items():
            if collector.has_error():
                item_result = collector.get_error_item()
            elif collector.has_not_found():
                item_result = collector.get_not_found_item()
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


class RailResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._rail = {}
        self._error = {}
        self._not_found = {}

    def collect_rail_item(self, item: rail_items.RailItem):
        clean_dict = self._clean_item(item)
        self._rail.update(clean_dict)

    def collect_not_found_item(self, item: DataNotFoundItem):
        clean_dict = self._clean_item(item)
        self._not_found.update(clean_dict)

    def collect_error_item(self, item: ExportErrorData):
        clean_dict = self._clean_item(item)
        self._error.update(clean_dict)

    def build_final_data(self) -> Optional[Dict]:
        if self._rail:
            return {
                "status": RESULT_STATUS_DATA,
                "request_args": self._request_args,
                "rail": self._rail,
            }

    def build_error_data(self, item: ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": RESULT_STATUS_FATAL,  # default status
            "request_args": self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: rail_items.DebugItem) -> Dict:
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
        return {k: v for k, v in item.items() if not k.startswith("_")}

    def is_default(self):
        return False if self._rail else True

    def has_not_found(self):
        return True if self._not_found else False

    def has_error(self):
        return True if self._error else False

    def get_error_item(self):
        self._error.update({"request_args": self._request_args})
        return self._error

    def get_not_found_item(self):
        self._not_found.update({"request_args": self._request_args})
        return self._not_found