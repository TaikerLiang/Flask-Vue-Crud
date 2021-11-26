import os
import pprint
import traceback
from typing import Dict, Union

from scrapy.exceptions import DropItem

from . import items as terminal_items
from .base import (
    TERMINAL_RESULT_STATUS_DATA,
    TERMINAL_RESULT_STATUS_FATAL,
    TERMINAL_RESULT_STATUS_DEBUG,
    TERMINAL_RESULT_STATUS_ERROR,
)
from crawler.services.edi_service import EdiClientService


class BaseItemPipeline:
    def __init__(self):
        # edi client setting
        user = os.environ.get("EDI_ENGINE_USER")
        token = os.environ.get("EDI_ENGINE_TOKEN")
        url = os.environ.get("EDI_ENGINE_URL")
        self.edi_client = EdiClientService(url=url, edi_user=user, edi_token=token)

    def handle_err_result(self, collector, task_id: int, result: Dict):
        if collector.is_default():
            status_code, text = self.edi_client.send_provider_result_back(
                task_id=task_id, provider_code="scrapy_cloud_api", item_result=result
            )
        else:
            item_result = collector.build_final_data()
            status_code, text = self.edi_client.send_provider_result_back(
                task_id=task_id, provider_code="scrapy_cloud_api", item_result=item_result
            )
        return status_code, text


class TerminalItemPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__()

    @classmethod
    def get_setting_name(cls):
        return f"{__name__}.{cls.__name__}"

    def open_spider(self, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- open_spider -----")

        self._collector = TerminalResultCollector(request_args=spider.request_args)

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

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
                raise DropItem(f"unknown item: {item}")

        except:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
            return self._collector.build_error_data(err_item)

        raise DropItem("item processed")


# ---------------------------------------------------------------------------------------------------------------------


class TerminalMultiItemsPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__()
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

            self._collector_map.setdefault(task_id, TerminalResultCollector(request_args=request_args))

    def process_item(self, item, spider):
        spider.logger.info(f"[{self.__class__.__name__}] ----- process_item -----")
        spider.logger.info(f"item : {pprint.pformat(item)}")

        default_collector = TerminalResultCollector(request_args=spider.request_args)

        try:
            collector = self._collector_map[item["task_id"]] if "task_id" in item else default_collector

            if isinstance(item, terminal_items.TerminalItem) or isinstance(item, terminal_items.InvalidDataFieldItem):
                collector.collect_terminal_item(item=item)
            elif isinstance(item, terminal_items.InvalidContainerNoItem):
                collector.collect_invalid_no_data(item=item)
            elif isinstance(item, terminal_items.ExportErrorData):
                collector.collect_error_item(item=item)
                # results = self._default_collector.build_error_data(item)
                # collector_results = self._get_results_of_collectors()
                # results = [results] + collector_results if collector_results else results
                # return {"results": results}
            elif isinstance(item, terminal_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, terminal_items.DebugItem):
                debug_data = default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f"unknown item: {item}")
        except:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
            result = default_collector.build_error_data(err_item)

            res = self._send_error_msg_back_to_edi_engine(result=result)
            return {"status": "CLOSE", "result": res}
            # collector_results = self._get_results_of_collectors()
            # results = [results] + collector_results if collector_results else results
            # return results

        raise DropItem("item processed")

    def _send_result_back_to_edi_engine(self):
        res = []
        for task_id, collector in self._collector_map.items():
            if collector.has_error():
                item_result = collector.get_error_item()
            else:
                item_result = collector.build_final_data()
            if item_result:
                status_code, text = self.edi_client.send_provider_result_back(
                    task_id=task_id, provider_code="scrapy_cloud_api", item_result=item_result
                )
                res.append({"task_id": task_id, "status_code": status_code, "text": text, "data": item_result})

        return res

    def _send_error_msg_back_to_edi_engine(self, result: Dict):
        res = []
        for task_id, collector in self._collector_map.items():
            status_code, text = self.handle_err_result(collector=collector, task_id=task_id, result=result)
            res.append({"task_id": task_id, "status_code": status_code, "text": text})

        return res

    # def _get_results_of_collectors(self):
    #     results = []
    #     for _, collector in self._collector_map.items():
    #         if not collector.is_item_empty():
    #             results.append(collector.build_final_data())

    #     return results


class TerminalResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._terminal = {}
        self._error = {}

    def collect_terminal_item(self, item: terminal_items.TerminalItem):
        clean_dict = self._clean_item(item)
        self._terminal.update(clean_dict)

    def collect_error_item(self, item: terminal_items.ExportErrorData):
        clean_dict = self._clean_item(item)
        self._error.update(clean_dict)

    def build_final_data(self) -> Union[Dict, None]:
        if self._terminal:
            return {
                "status": TERMINAL_RESULT_STATUS_DATA,
                "request_args": self._request_args,
                "terminal": self._terminal,
            }

    def build_error_data(self, item: terminal_items.ExportErrorData) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": TERMINAL_RESULT_STATUS_FATAL,  # default status
            "request_args": self._request_args,
            **clean_dict,
        }

    def build_debug_data(self, item: terminal_items.DebugItem) -> Dict:
        clean_dict = self._clean_item(item)

        return {
            "status": TERMINAL_RESULT_STATUS_DEBUG,
            **clean_dict,
        }

    def build_invalid_no_data(self, item: terminal_items.InvalidContainerNoItem) -> Dict:

        return {
            "status": TERMINAL_RESULT_STATUS_ERROR,  # default status
            "request_args": self._request_args,
            "invalid_container_no": item["container_no"],
            "task_id": item["task_id"],
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {k: v for k, v in item.items() if not k.startswith("_")}

    def has_error(self):
        return True if self._error else False

    def get_error_item(self):
        self._error.update({"request_args": self._request_args})
        return self._error
