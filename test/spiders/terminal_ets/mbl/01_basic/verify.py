from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        vessel='EVER ENVOY',
        mbl_no='002000261242',
        voyage='0012-159E',
    )
