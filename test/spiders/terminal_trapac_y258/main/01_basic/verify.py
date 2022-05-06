from typing import List

from crawler.core_terminal.items_new import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no="GAOU6334583",
        last_free_day="08/24/2021",
        customs_release="Released",
        demurrage="$-245.00",
        container_spec="40/SD/96",
        holds="No",
        cy_location="In Yard (#B004 row) Grounded",
        vessel="HJK",
        voyage="112E",
    )
