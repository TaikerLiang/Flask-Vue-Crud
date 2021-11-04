from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        mbl_no="QSWB801163", status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found"
    )
