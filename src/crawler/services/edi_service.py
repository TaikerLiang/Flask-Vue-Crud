import os
from typing import Dict, List, Tuple

import requests
import ujson as json


class EdiClientService:
    def __init__(self, edi_user: str, edi_token: str) -> List:
        self.url = os.environ.get('EDI_ENGINE_URL')
        self.edi_user = edi_user
        self.edi_token = edi_token

    def get_active_task_by_scac_code(self, scac_code: str):
        response = requests.request("GET", f'{self.url}?scac_code={scac_code}', headers=self.build_header())
        content = response.json()
        return content['rows']

    def build_header(self) -> Dict:
        return {
            'HEDI-SENDER': self.edi_user,
            'HEDI-AUTHORIZATION': f'AuthToken {self.edi_token}',
            'Host': os.environ.get('EDI_HOST')
        }

    def send_provider_result_back(self, task_id: int, provider_code: str, result: Dict) -> Tuple[int, str]:
        data = {
            'provider_code': provider_code,
            'task_id': task_id,
            'result_data': json.dumps(result),
        }

        resp = requests.post(url=self.url, data=data, headers=self.build_header())

        return resp.status_code, resp.text


class EdiDataHandler:
    @staticmethod
    def build_response_data(task_id: int, spider_tag: str, result: Dict) -> Dict:
        return {
            'task_id': task_id,
            'job_key': '-',
            'spider': spider_tag,
            'close_reason': '',
            'items': [result],
        }
