from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        task_id='1',
        detail='Data was not found',
        mbl_no='999455999',
        status=CARRIER_RESULT_STATUS_ERROR,
    )
