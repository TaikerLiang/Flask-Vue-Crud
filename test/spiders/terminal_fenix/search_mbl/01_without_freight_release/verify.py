from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        freight_release='Released',
        customs_release='Released',
        carrier='OCL',
        mbl_no='2638732540',
        voyage='WGT0TX5U',
    )
