from typing import List

from crawler.core_air.exceptions import AIR_RESULT_STATUS_ERROR
from crawler.core_air.items import ExportErrorData


def verify(results: List):
    assert results[0] == ExportErrorData(
        status=AIR_RESULT_STATUS_ERROR,
        detail="<invalid-mawb-no>",
    )
