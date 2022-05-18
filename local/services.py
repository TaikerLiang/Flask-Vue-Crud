from collections import defaultdict
from math import ceil
from typing import List

from local.defines import AggregatePagingNum, LocalTask


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
