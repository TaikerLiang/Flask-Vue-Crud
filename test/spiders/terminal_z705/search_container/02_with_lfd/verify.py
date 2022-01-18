from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='YMMU6297676',
        ready_for_pick_up='Delivered',
        customs_release='Released()',
        carrier_release='Released',
        appointment_date=None,
        last_free_day='08-11-2021',
        container_spec='DC 40 96',
        holds='',
        cy_location='Out-Gated (08/12/2021 15:27)',
    )
