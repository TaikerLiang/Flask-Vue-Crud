from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no='KKFU7819122',
        last_free_day='N/A',
        customs_release='Released',
        demurrage='$0.00',
        container_spec='40/SD/96',
        holds='N/A',
        cy_location='In Yard (C row) Grounded',
        vessel='CNP',
        voyage='010E',
    )
