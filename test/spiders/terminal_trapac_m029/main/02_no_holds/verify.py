from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no='DRYU4301406',
        last_free_day='N/A',
        customs_release='N/A',
        demurrage='$0.00',
        container_spec='40/SD/86',
        holds='N/A',
        cy_location='Delivered 08/19/2021 16:33',
        vessel='HKI',
        voyage='045E',
    )
