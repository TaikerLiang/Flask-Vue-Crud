from typing import List

from crawler.core_terminal.items import ExportErrorData
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR


def verify(results: List):
    assert results[0] == ExportErrorData(
        container_no="BMOU6053191",
        status=TERMINAL_RESULT_STATUS_ERROR,
        detail="Data was not found",
    )
