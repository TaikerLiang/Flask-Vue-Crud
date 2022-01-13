from typing import List

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL
from crawler.core_terminal.items import ExportErrorData


def verify(results: List):
    assert results[0] == ExportErrorData(
        status=TERMINAL_RESULT_STATUS_FATAL,
        detail="Target container_no does not meet the container_no that website shows",
    )
