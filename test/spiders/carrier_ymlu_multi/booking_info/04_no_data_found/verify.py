from typing import List

from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results: List):
    assert results[0] == ExportErrorData(
        task_id=1,
        booking_no='FCL147384',
        detail='Data was not found',
        status=CARRIER_RESULT_STATUS_ERROR,
    )
