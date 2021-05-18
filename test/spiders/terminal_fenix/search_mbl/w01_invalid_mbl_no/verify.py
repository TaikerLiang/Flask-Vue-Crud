from typing import List

from crawler.spiders.terminal_fenix import WarningMessage


def verify(results: List):
    assert results[0] == WarningMessage(msg='[SEARCH_MBL] ----- handle -> mbl_no is invalid : `263873254`')
