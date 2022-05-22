import pprint
import traceback
from typing import Dict, Optional

from scrapy.exceptions import DropItem

from crawler.core.pipelines import BaseItemPipeline
from crawler.core_terminal import items as terminal_items
from crawler.core_terminal.base import (
    TERMINAL_RESULT_STATUS_DATA,
    TERMINAL_RESULT_STATUS_DEBUG,
    TERMINAL_RESULT_STATUS_ERROR,
    TERMINAL_RESULT_STATUS_FATAL,
)


class TerminalItemPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-terminal/local/")

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
            elif isinstance(item, terminal_items.InvalidItem):
                self._collector.collect_invalid_data(item=item)
            elif isinstance(item, terminal_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, terminal_items.DebugItem):
                return self._collector.build_debug_data(item)
            else:
                raise DropItem(f"unknown item: {item}")

        except Exception:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
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


class TerminalMultiItemsPipeline(BaseItemPipeline):
    def __init__(self):
        super().__init__("tracking-terminal/local/")
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

            if isinstance(item, terminal_items.TerminalItem):
                collector.collect_terminal_item(item=item)
            elif isinstance(item, terminal_items.InvalidItem):
                collector.collect_invalid_data(item=item)
            elif isinstance(item, terminal_items.ExportErrorData):
                collector.collect_error_item(item=item)
            elif isinstance(item, terminal_items.ExportFinalData):
                res = self._send_result_back_to_edi_engine()
                return {"status": "CLOSE", "result": res}
            elif isinstance(item, terminal_items.DebugItem):
                debug_data = default_collector.build_debug_data(item)
                return debug_data
            else:
                raise DropItem(f"unknown item: {item}")
        except Exception:
            spider.mark_error()
            status = TERMINAL_RESULT_STATUS_FATAL
            detail = traceback.format_exc()
            err_item = terminal_items.ExportErrorData(status=status, detail=detail)
            result = default_collector.build_error_data(err_item)

            res = self._send_error_msg_back_to_edi_engine(result=result)
            return {"status": "CLOSE", "result": res}

        raise DropItem("item processed")

    def _send_result_back_to_edi_engine(self):
        res = []
        for task_id, collector in self._collector_map.items():
            if collector.has_error():
                item_result = collector.get_error_item()
            elif collector.has_invalid():
                item_result = collector.build_invalid_data()
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


# ---------------------------------------------------------------------------------------------------------------------


class TerminalResultCollector:
    def __init__(self, request_args):
        self._request_args = dict(request_args)
        self._terminal = {}
        self._invalid = {}
        self._error = {}

    def collect_terminal_item(self, item: terminal_items.TerminalItem):
        clean_dict = self._clean_item(item)
        self._terminal.update(clean_dict)

    def collect_invalid_data(self, item: terminal_items.InvalidItem):
        clean_dict = self._clean_item(item)
        self._invalid.update(clean_dict)

    def collect_error_item(self, item: terminal_items.ExportErrorData):
        clean_dict = self._clean_item(item)
        self._error.update(clean_dict)

    def build_final_data(self) -> Optional[Dict]:
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

    def build_invalid_data(self) -> Dict:
        return {
            "status": TERMINAL_RESULT_STATUS_ERROR,  # default status
            "request_args": self._request_args,
            "invalid": self._invalid,
        }

    @staticmethod
    def _clean_item(item):
        """
        drop private keys (startswith '_')
        """
        return {k: v for k, v in item.items() if not k.startswith("_")}

    def is_default(self):
        return False if self._terminal else True

    def has_invalid(self):
        return True if self._invalid else False

    def has_error(self):
        return True if self._error else False

    def get_error_item(self):
        self._error.update({"request_args": self._request_args})
        return self._error
