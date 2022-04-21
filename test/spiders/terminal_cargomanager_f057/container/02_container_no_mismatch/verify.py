from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL
from crawler.core_terminal.items import ExportErrorData


def verify(results):
    assert results[0] == ExportErrorData(
        container_no="SEGU5842736",
        status=TERMINAL_RESULT_STATUS_FATAL,
        detail="Target container_no does not meet the container_no that website shows",
    )
