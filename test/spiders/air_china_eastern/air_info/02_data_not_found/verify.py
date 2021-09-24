from crawler.core_air.items import ExportErrorData
from crawler.core_air.exceptions import AIR_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        detail='Data was not found',
        status=AIR_RESULT_STATUS_ERROR,
    )

