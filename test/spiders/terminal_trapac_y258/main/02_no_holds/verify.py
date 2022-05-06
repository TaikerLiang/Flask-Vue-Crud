from typing import List

from crawler.core_terminal.items_new import TerminalItem
from crawler.core_terminal.trapac_share_spider import SaveItem


def verify(results: List):
    assert isinstance(results[0], SaveItem)

    assert results[1] == TerminalItem(
        container_no="TGHU6961213",
        last_free_day="N/A",
        customs_release="N/A",
        demurrage="$0.00",
        container_spec="40/SD/96",
        holds="N/A",
        cy_location="Delivered 07/26/2021 19:35",
        vessel="FLV",
        voyage="001E",
    )
