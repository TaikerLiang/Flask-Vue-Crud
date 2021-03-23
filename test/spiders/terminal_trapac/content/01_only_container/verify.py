from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.spiders.terminal_trapac import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no='YMMU4127027',
        last_free_day='N/A',
        customs_release=None,
        # demurrage='$0.00',
        # container_spec='40/SD/86',
        # holds='N/A',
        # cy_location='Delivered 08/31/2020 18:02',
        # vessel='KUX',
        # voyage='084E',
        # carrier=None,
        # mbl_no=None,
    )

