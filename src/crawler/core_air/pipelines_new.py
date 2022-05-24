import pprint
import traceback
from typing import Dict, Optional

from scrapy.exceptions import DropItem

from crawler.core.base_new import (
    RESULT_STATUS_DATA,
    RESULT_STATUS_DEBUG,
    RESULT_STATUS_FATAL,
)
from crawler.core.exceptions_new import DidNotEndError
from crawler.core.items_new import DataNotFoundItem, EndItem, ExportErrorData
from crawler.core.pipelines import BaseItemPipeline
from crawler.core_air import items_new as air_items


class AirItemPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-airline/local/")

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        self._collector = AirResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        try:
            if isinstance(item, air_items.AirItem):
                self._collector.collect_air_item(item=item)
            elif isinstance(item, air_items.FlightItem):
                self._collector.collect_flight_item(item=item)
            elif isinstance(item, air_items.HistoryItem):
                self._collector.collect_history_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                self._collector.collect_not_found_item(item=item)
            elif isinstance(item, EndItem):
                self._collector.set_is_end()
            elif isinstance(item, air_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine(spider=spider)
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, air_items.DebugItem):
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
            res.append({"task_id": task_id, "status_code": status_code, "text": text})
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


class AirMultiItemsPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-airline/local/")
        self._collector_map = {}

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        for task_id, mawb_no in zip(spider.task_ids, spider.mawb_nos):
            self._collector_map.setdefault(
                task_id,
                AirResultCollector(
                    request_args={
                        "task_id": task_id,
                        "mawb_no": mawb_no,
                        "save": spider.request_args.get("save"),
                    }
                ),
            )

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        self._default_collector = AirResultCollector(request_args=spider.request_args)

        try:
            collector = self._collector_map[item["task_id"]] if "task_id" in item else self._default_collector

            if isinstance(item, air_items.AirItem):
                collector.collect_air_item(item=item)
            elif isinstance(item, air_items.FlightItem):
                collector.collect_flight_item(item=item)
            elif isinstance(item, air_items.HistoryItem):
                collector.collect_history_item(item=item)
            elif isinstance(item, DataNotFoundItem):
                collector.collect_not_found_item(item=item)
            elif isinstance(item, EndItem):
                collector.set_is_end()
            elif isinstance(item, air_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, ExportErrorData):
                collector.collect_error_item(item=item)
            elif isinstance(item, air_items.DebugItem):
                debug_data = self._default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f"unknown item: {item}")

        except Exception:
            spider.mark_error()
            status = RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = ExportErrorData(status=status, detail=detail)

            result = self._default_collector.build_error_data(err_item)
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


class AirResultCollector:
    def __init__(self, request_args):
        self._is_end = False
        self._request_args = dict(request_args)
        self._air = {}
        self._flights = []
        self._history = []
        self._not_found = {}
        self._error = {}

    def collect_air_item(self, item: air_items.AirItem):
        clean_item = self._clean_item(item)
        self._air.update(clean_item)

    def collect_flight_item(self, item: air_items.FlightItem):
        clean_item = self._clean_item(item)
        self._flights.append(clean_item)

    def collect_history_item(self, item: air_items.HistoryItem):
        clean_item = self._clean_item(item)
        self._history.append(clean_item)

    def collect_not_found_item(self, item: DataNotFoundItem):
        clean_dict = self._clean_item(item)
        self._not_found.update(clean_dict)

    def collect_error_item(self, item: ExportErrorData):
        clean_dict = self._clean_item(item)
        self._error.update(clean_dict)

    def build_final_data(self) -> Optional[Dict]:
        if self._air or self._flights or self._history:
            return {
                "status": RESULT_STATUS_DATA,
                "request_args": self._request_args,
                "air": self._air,
                "flights": self._flights,
                "history": self._history,
            }

    def build_error_data(self, item: ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": RESULT_STATUS_FATAL,  # default status
            "request_args": self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: air_items.DebugItem) -> Dict:
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

    def set_is_end(self):
        self._is_end = True

    def is_end(self):
        return self._is_end

    def is_default(self):
        return not bool(self._air)

    def has_not_found(self):
        return bool(self._not_found)

    def has_error(self):
        return bool(self._error)

    def get_error_item(self):
        item = self._error.copy()
        item.update({"request_args": self._request_args})
        return item

    def get_not_found_item(self):
        item = self._not_found.copy()
        item.update({"request_args": self._request_args})
        return item

    def is_item_empty(self) -> bool:
        return not bool(self._air)

    @staticmethod
    def _get_default(task_id: str):
        return {
            "task_id": task_id,
        }
