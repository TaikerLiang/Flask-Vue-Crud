from typing import List

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData


def verify(results: List):
    assert results[0] == ExportErrorData(
        container_no="TGCU0160986",
        detail="Data was not found",
        status=TERMINAL_RESULT_STATUS_ERROR,
    )
