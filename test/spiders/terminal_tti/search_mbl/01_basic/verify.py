from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        mbl_no='MEDUQ3514583',
        vessel='CAP SAN JUAN',
        voyage='038N',
    )
