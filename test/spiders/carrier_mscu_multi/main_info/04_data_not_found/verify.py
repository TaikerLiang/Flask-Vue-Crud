from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        task_id="1",
        mbl_no="MEDUMY898252",
        status=CARRIER_RESULT_STATUS_ERROR,
        detail="Data was not found",
    )
