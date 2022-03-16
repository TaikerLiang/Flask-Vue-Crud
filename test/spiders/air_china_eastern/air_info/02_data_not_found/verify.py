from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_AWB
from crawler.core.items import DataNotFoundItem


def verify(results):
    assert results[0] == DataNotFoundItem(
        task_id="1",
        search_no="81375673",
        search_type=SEARCH_TYPE_AWB,
        detail="Data was not found",
        status=RESULT_STATUS_ERROR,
    )
