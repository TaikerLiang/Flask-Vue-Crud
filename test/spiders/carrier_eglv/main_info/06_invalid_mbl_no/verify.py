from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.items import DataNotFoundItem


class Verifier:
    def verify(self, results):
        assert results[0] == DataNotFoundItem(
            task_id="1",
            search_no="003901796617",
            search_type=SEARCH_TYPE_MBL,
            status=RESULT_STATUS_ERROR,
            detail="Data was not found",
        )
