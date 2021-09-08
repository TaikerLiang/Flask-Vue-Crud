from typing import Dict, List
from math import ceil
from collections import defaultdict

from local.defines import AggregatePagingNum, LocalTask


class DataHandler:
    def build_init_item_response(self, spider_tag, task_ids, mbl_nos, booking_nos, container_nos) -> Dict:
        task_id_list = task_ids.split(",")
        resp = {}
        for task_id in task_id_list:
            resp.update(
                {
                    task_id: {
                        "status": "",
                        "request_args": {
                            "task_ids": task_ids,
                            "mbl_nos": mbl_nos,
                            "booking_nos": booking_nos,
                            "container_nos": container_nos,
                            "task_category": spider_tag,
                        },
                    }
                }
            )

        return resp

    def build_response_data(self, _type: str, items: List) -> List:
        if _type == "carrier":
            return list(self._build_carrier_resp(items=items))
        elif _type == "terminal":
            return list(self._build_terminal_resp(items=items))
        elif _type == "rail":
            pass

    def _build_carrier_resp(self, items: List):
        data_result = {"basic": {}, "vessels": [], "containers": []}
        containers = {}  # container_no: container_info

        for item in items:
            item = self._scrapy_item_to_dict(item)
            if "task_id" in item:
                data_result.update(item)

            if "mbl_no" in item:
                data_result["basic"] = item

            elif "container_key" in item:
                container_key = item["container_key"]
                containers.setdefault(container_key, {})

                if "container_no" in item:
                    containers[container_key].update(item)
                else:
                    containers[container_key].setdefault("status", [])
                    containers[container_key]["status"].append(item)

            elif "vessel_key" in item:
                data_result["vessels"].append(item)

        for container_no, container_info in containers.items():
            data_result["containers"].append(container_info)

        self._clear_dict_value_to_none(dictt=data_result, value_kinds=[None, ""])

        yield data_result

    def _build_terminal_resp(self, items: List):
        for item in items:
            yield {"task_id": item["task_id"], "terminal": {**item}}

    def _scrapy_item_to_dict(self, item) -> Dict:
        if isinstance(item, dict):
            return item

        item = dict(item)

        for k, v in item.items():
            if isinstance(v, (str, int)) or not v:
                continue
            item[k] = dict(v)

        return item

    def update_resp_data(self, data: Dict, result: Dict) -> Dict:
        tmp_result = result.copy()
        tmp_result.update(
            {"status": "DATA", **data,}
        )

        return tmp_result

    @staticmethod
    def update_error_message(result: Dict, err_msg: str) -> Dict:
        tmp_result = result.copy()
        tmp_result["close_reason"] = "ERROR"
        tmp_result["items"][0].update(
            {"status": "ERROR", "detail": err_msg,}
        )

        return tmp_result

    def _clear_dict_value_to_none(self, dictt: Dict, value_kinds: List):
        # TODO: refactor parameter name
        for key, value in dictt.items():
            if isinstance(value, dict):
                self._clear_dict_value_to_none(dictt=value, value_kinds=value_kinds)
            elif value in value_kinds:
                dictt[key] = None


class TaskAggregator:
    def aggregate_tasks(self, tasks: List):
        mapping_table = defaultdict(list)
        for task in tasks:
            if task.get("type", "") == "carrier":
                key = f"{task.get('type', '')}-{task.get('scac_code', '')}"
            elif task.get("type", "") == "terminal":
                key = f"{task.get('type', '')}-{task.get('firms_code', '')}"
            else:
                continue
            mapping_table[key].append(task)

        paging_num = 1
        res = defaultdict(list)
        for key, items in mapping_table.items():
            if "carrier" in key:
                paging_num = AggregatePagingNum.CARRIER
            elif "terminal" in key:
                paging_num = AggregatePagingNum.TERMINAL
            elif "rail" in key:
                paging_num = AggregatePagingNum.RAIL

            res[key] = self._get_local_tasks(key, items, paging_num)

        return res

    @staticmethod
    def _get_local_tasks(key: str, items: List, paging_num: int):
        res = []
        for r in range(ceil(len(items) / paging_num)):
            task_ids, mbl_nos, booking_nos, container_nos = [], [], [], []
            for i in range(paging_num):
                if (r * paging_num + i) == len(items):
                    break
                task_ids.append(items[r * paging_num + i].get("task_id", ""))
                mbl_nos.append(items[r * paging_num + i].get("mbl_no", ""))
                booking_nos.append(items[r * paging_num + i].get("booking_no", ""))
                container_nos.append(items[r * paging_num + i].get("container_no", ""))

            local_task = LocalTask(
                code=key, task_ids=task_ids, mbl_nos=mbl_nos, booking_nos=booking_nos, container_nos=container_nos
            )
            res.append(local_task)

        return res
