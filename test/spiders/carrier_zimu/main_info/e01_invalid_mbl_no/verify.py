from crawler.core.base_new import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.items_new import DataNotFoundItem


def verify(results):
    assert results == [
        DataNotFoundItem(
            task_id="1",
            search_no="ZIMUSNH110567",
            search_type=SEARCH_TYPE_MBL,
            status=RESULT_STATUS_ERROR,
            detail="Data was not found",
        ),
    ]