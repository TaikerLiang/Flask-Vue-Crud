from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no='TTNU8130668',
        last_free_day='N/A',
        customs_release='N/A',
        demurrage='$0.00',
        container_spec='40/RF/96',
        holds='N/A',
        cy_location='',
        vessel='HFC',
        voyage='090E',
    )
