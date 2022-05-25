from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="FFAU1577392",
        container_spec="Standard 40' 9'6\"",
        customs_release="Missing",
        cy_location="Out-Gated (08/20/2021 09:21)",
        yard_location="Out-Gated (08/20/2021 09:21)",
        ready_for_pick_up="-",
        available="-",
        appointment_date="Not an Import Container",
        carrier_release="Missing",
        holds="",
        last_free_day="",
    )
