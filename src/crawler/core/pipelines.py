import os
from typing import Dict

from crawler.services.edi_service import EdiClientService


class BaseItemPipeline:
    def __init__(self, url_suffix: str):
        # edi client setting
        user = os.environ.get("EDI_ENGINE_USER") or ""
        token = os.environ.get("EDI_ENGINE_TOKEN") or ""
        url = f'{os.environ.get("EDI_ENGINE_BASE_URL") or ""}{url_suffix}'
        self._edi_client = EdiClientService(url=url, edi_user=user, edi_token=token)
        self._provider_code = "scrapy_local" if os.environ.get("RUNNING_AT") == "local" else "scrapy_cloud_api"
        self._mode = os.environ.get("RUNNING_MODE") or "prd"

    def send_provider_result_to_edi_client(self, task_id: int, item_result: Dict):
        if self._mode != "prd":
            return "200", "Ignored due to dev mode"

        return self._edi_client.send_provider_result_back(
            task_id=task_id, provider_code=self._provider_code, item_result=item_result
        )

    def handle_err_result(self, collector, task_id: int, result: Dict):
        item_result = result if collector.is_default() else collector.build_final_data()
        return self.send_provider_result_to_edi_client(task_id=task_id, item_result=item_result)
