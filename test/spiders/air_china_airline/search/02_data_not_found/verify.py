from typing import List

from crawler.core_air.exceptions import AIR_RESULT_STATUS_ERROR
from crawler.core_air.items import ExportErrorData


def verify(results: List):
    assert results[0] == ExportErrorData(
        task_id="2",
        mawb_no="16830165",
        status=AIR_RESULT_STATUS_ERROR,
        detail="Data was not found",
    )
