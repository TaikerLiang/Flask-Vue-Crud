from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        freight_release='BL LINE HOLD',
        customs_release='Released',
        carrier='EGR',
        mbl_no='146000297601',
        voyage='NOR0TX62',
    )
