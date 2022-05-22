import pprint
import traceback
from typing import Dict, Union

from scrapy.exceptions import DropItem

from crawler.core.pipelines import BaseItemPipeline

from . import items as air_items
from .base import (
    AIR_RESULT_STATUS_DATA,
    AIR_RESULT_STATUS_DEBUG,
    AIR_RESULT_STATUS_FATAL,
)


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
            elif isinstance(item, air_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, air_items.ExportErrorData):
                return self._collector.build_error_data(item)
            elif isinstance(item, air_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f"unknown item: {item}")

        except:  # noqa: E722
            spider.mark_error()
            status = AIR_RESULT_STATUS_FATAL
            detail = traceback.format_exc()

            err_item = air_items.ExportErrorData(status=status, detail=detail)
            result = self._collector.build_error_data(err_item)
            res = self._send_error_msg_back_to_edi_engine(result=result)
            return {"status": "CLOSE", "result": res}

        raise DropItem("item processed")

    def _send_result_back_to_edi_engine(self):
        res = []
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


class AirMultiItemsPipeline:
    def __init__(self):
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
            if isinstance(item, air_items.AirItem):
                collector = self._collector_map[item.key] if item.key else self._default_collector
                collector.collect_air_item(item=item)
                return collector.build_final_data()
            elif isinstance(item, air_items.FlightItem):
                collector = self._collector_map[item.key] if item.key else self._default_collector
                collector.collect_flight_item(item=item)
                return collector.build_final_data()
            elif isinstance(item, air_items.HistoryItem):
                collector = self._collector_map[item.key] if item.key else self._default_collector
                collector.collect_history_item(item=item)
                return collector.build_final_data()
            elif isinstance(item, air_items.ExportFinalData):
                return {"status": "CLOSE"}
            elif isinstance(item, air_items.ExportErrorData):
                results = self._default_collector.build_error_data(item)
                collector_results = self._get_results_of_collectors()
                results = [results] + collector_results if collector_results else results
                return {"results": results}
            elif isinstance(item, air_items.DebugItem):
                debug_data = self._default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f"unknown item: {item}")

        except:  # noqa: E722
            spider.mark_error()
            status = AIR_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = air_items.ExportErrorData(status=status, detail=detail)

            results = self._default_collector.build_error_data(err_item)
            collector_results = self._get_results_of_collectors()
            results = [results] + collector_results if collector_results else results
            return results

        raise DropItem("item processed")

    def _get_results_of_collectors(self):
        results = []
        for _, collector in self._collector_map.items():
            if not collector.is_item_empty():
                results.append(collector.build_final_data())

        return results


class AirResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._air = {}
        self._flights = []
        self._history = []

    def collect_air_item(self, item: air_items.AirItem):
        clean_item = self._clean_item(item)
        self._air.update(clean_item)

    def collect_flight_item(self, item: air_items.FlightItem):
        clean_item = self._clean_item(item)
        self._flights.append(clean_item)

    def collect_history_item(self, item: air_items.HistoryItem):
        clean_item = self._clean_item(item)
        self._history.append(clean_item)

    def build_final_data(self) -> Union[Dict, None]:
        if self._air or self._flights or self._history:
            return {
                "status": AIR_RESULT_STATUS_DATA,
                "request_args": self._request_args,
                "air": self._air,
                "flights": self._flights,
                "history": self._history,
            }

    def build_error_data(self, item: air_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": AIR_RESULT_STATUS_FATAL,  # default status
            "request_args": self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: air_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": AIR_RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {k: v for k, v in item.items() if not k.startswith("_")}

    def is_default(self):
        return False if self._air else True

    def is_item_empty(self) -> bool:
        return not bool(self._air)

    @staticmethod
    def _get_default(task_id: str):
        return {
            "task_id": task_id,
        }
