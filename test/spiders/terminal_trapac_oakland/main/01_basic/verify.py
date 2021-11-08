from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no='HLBU2708375',
        last_free_day='08/30/2021',
        customs_release='Released',
        demurrage='$0.00',
        container_spec='40/SD/96',
        holds='No',
        cy_location='In Yard (W row) On Wheels',
        vessel='YUF',
        voyage='219E',
    )
