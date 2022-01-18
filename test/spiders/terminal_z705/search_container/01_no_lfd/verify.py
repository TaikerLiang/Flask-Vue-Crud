from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='TGBU4645596',
        ready_for_pick_up='No',
        customs_release='Missing',
        carrier_release='Missing',
        appointment_date=None,
        last_free_day='',
        container_spec='DC 40 96',
        holds='',
        cy_location='Out-Gated (08/29/2021 14:05)',
    )
