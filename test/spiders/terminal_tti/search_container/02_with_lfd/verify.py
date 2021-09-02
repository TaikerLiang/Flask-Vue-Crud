from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="CAIU4399890",
        container_spec="Standard 40' 9'6\"",
        customs_release="Released",
        cy_location="Out-Gated (08/31/2021 14:58)",
        ready_for_pick_up="Delivered",
        appointment_date="08-31-2021 14:00~15:00",
        carrier_release="Released",
        holds="",
        last_free_day="08-31-2021",
    )
