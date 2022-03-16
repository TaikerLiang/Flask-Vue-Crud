from typing import List

from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_AWB
from crawler.core.items import DataNotFoundItem


def verify(results: List):
    assert results[0] == DataNotFoundItem(
        task_id="1",
        search_no="46449060",
        search_type=SEARCH_TYPE_AWB,
        status=RESULT_STATUS_ERROR,
        detail="Data was not found",
    )
