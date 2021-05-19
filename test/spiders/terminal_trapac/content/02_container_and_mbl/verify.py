from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.spiders.terminal_trapac import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)
    assert isinstance(results[1], SaveItem)

    assert results[2] == TerminalItem(
        container_no='KOCU4427065',
        last_free_day='N/A',
        customs_release='Released',
        # cy_location='Delivered 08/22/2020 08:05',
        # holds='N/A',
        # demurrage='$0.00',
        # container_spec='40/SD/96',
        # vessel='NAC',
        # voyage='051E',
        # mbl_no='NXWB7009876',
        # carrier='Released',
    )
