from crawler.core.base_new import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.items_new import DataNotFoundItem


def verify(results):
    assert results[0] == DataNotFoundItem(
        task_id="1",
        search_type=SEARCH_TYPE_MBL,
        search_no="MEDUMY898252",
        status=RESULT_STATUS_ERROR,
        detail="Data was not found",
    )
