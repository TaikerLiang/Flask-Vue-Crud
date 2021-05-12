from typing import List

from crawler.spiders.terminal_tos import WarningMessage


def verify(results: List):
    assert results[0] == WarningMessage(msg='[MBL_DETAIL] ----- handle -> mbl_no is invalid : `YMLUW2021298`')
