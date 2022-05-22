from crawler.core_terminal.items import ExportErrorData
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        container_no="EISU3920168",
        detail="Data was not found",
        status=TERMINAL_RESULT_STATUS_ERROR,
    )
