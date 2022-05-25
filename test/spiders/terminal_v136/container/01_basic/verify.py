from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        available="NO",
        container_no="EITU1744546",
        holds="CUSTOMS DEFAULT HOLD",
        customs_release="HOLD",
        carrier_release="RELEASED",
        last_free_day="",
        yard_location="V-ATT-0PGA4W1MA-340204",
    )
