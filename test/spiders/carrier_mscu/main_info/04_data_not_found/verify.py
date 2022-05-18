from crawler.core.base_new import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.description import DATA_NOT_FOUND_DESC
from crawler.core.items_new import DataNotFoundItem


def verify(results):
    assert results[0] == DataNotFoundItem(
        search_type=SEARCH_TYPE_MBL,
        search_no="MEDUMY898252",
        task_id="1",
        status=RESULT_STATUS_ERROR,
        detail=DATA_NOT_FOUND_DESC,
    )
