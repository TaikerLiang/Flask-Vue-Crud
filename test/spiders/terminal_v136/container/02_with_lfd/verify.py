from typing import List

from crawler.core_terminal.items import TerminalItem

def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='APZU3951656',
        holds='',
        customs_release='RELEASED',
        carrier_release='RELEASED',
        last_free_day='8/22/2021',
    )
