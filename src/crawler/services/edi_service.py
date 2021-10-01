from typing import Dict, List, Tuple
import os

import requests
import ujson as json


class EdiClientService:
    def __init__(self, url: str, edi_user: str, edi_token: str) -> List:
        self.url = url
        self.edi_user = edi_user
        self.edi_token = edi_token

    def get_active_task_by_scac_code(self, scac_code: str):
        response = requests.request("GET", f"{self.url}?scac_code={scac_code}", headers=self.build_header())
        content = response.json()
        return content["rows"]

    def build_header(self) -> Dict:
        return {
            "HEDI-SENDER": self.edi_user,
            "HEDI-AUTHORIZATION": f"AuthToken {self.edi_token}",
            "Host": os.environ.get("EDI_HOST"),
        }

    def send_provider_result_back(self, task_id: int, provider_code: str, item_result: Dict) -> Tuple[int, str]:
        data = self._build_provider_result(task_id=task_id, provider_code=provider_code, item_result=item_result)
        resp = requests.post(url=self.url, data=data, headers=self.build_header())

        return resp.status_code, resp.text

    def _build_provider_result(self, task_id: int, provider_code: str, item_result: Dict) -> Dict:
        result_data = {
            "task_id": task_id,
            "job_key": "-",
            "spider": "scrapy_cloud_api",
            "close_reason": "",
            "items": [item_result],
        }

        return {
            "provider_code": provider_code,
            "task_id": task_id,
            "result_data": json.dumps(result_data),
        }

    def get_local_tasks(self):
        response = requests.request("GET", f"{self.url}", headers=self.build_header())

        content = response.json()
        return content["rows"]
