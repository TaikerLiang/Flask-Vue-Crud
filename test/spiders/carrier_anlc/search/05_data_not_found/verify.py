from typing import List

from crawler.core.base_new import SEARCH_TYPE_MBL
from crawler.core.description import DATA_NOT_FOUND_DESC
from crawler.core.exceptions_new import RESULT_STATUS_ERROR
from crawler.core.items_new import DataNotFoundItem


def verify(results: List):

    assert results[0] == DataNotFoundItem(
        task_id="1",
        search_no="ATLHKN2119001",
        search_type=SEARCH_TYPE_MBL,
        status=RESULT_STATUS_ERROR,
        detail=DATA_NOT_FOUND_DESC,
    )


def multi_verify(results: List):

    assert results[0] == DataNotFoundItem(
        task_id="1",
        search_no="ATLHKN2119001",
        search_type=SEARCH_TYPE_MBL,
        status=RESULT_STATUS_ERROR,
        detail=DATA_NOT_FOUND_DESC,
    )
