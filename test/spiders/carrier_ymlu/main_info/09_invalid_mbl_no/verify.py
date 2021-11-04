from typing import List

from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results: List):
    assert results[0] == ExportErrorData(
        mbl_no="I209383517", status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found"
    )
