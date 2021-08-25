from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.items import ExportErrorData


def verify(results):
    assert results[0] == ExportErrorData(
                mbl_no='SITDSHSGZ02418',
                status=CARRIER_RESULT_STATUS_ERROR,
                detail='Data was not found'
            )
