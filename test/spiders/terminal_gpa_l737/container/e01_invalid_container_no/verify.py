from typing import List, Dict

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData


def verify(results: List[Dict]):
    assert results[0] == ExportErrorData(
        container_no="QQQQQQQQQQQQ",
        detail="Data was not found",
        status=TERMINAL_RESULT_STATUS_ERROR,
    )
