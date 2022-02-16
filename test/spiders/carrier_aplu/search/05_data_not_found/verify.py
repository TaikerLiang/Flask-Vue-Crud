from typing import List

from crawler.core_carrier.exceptions import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.items import ExportErrorData


def verify(results: List):

    assert results[0] == ExportErrorData(
        mbl_no="ATLHKN2119001",
        status=CARRIER_RESULT_STATUS_ERROR,
        detail="Data was not found",
    )


def multi_verify(results: List):

    assert results[0] == ExportErrorData(
        mbl_no="ATLHKN2119001",
        status=CARRIER_RESULT_STATUS_ERROR,
        detail="Data was not found",
        task_id=1,
    )
