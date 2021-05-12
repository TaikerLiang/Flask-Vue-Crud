from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='MSDU1314937',
        carrier='MSCU',
        ready_for_pick_up='Delivered',
        customs_release='Released',
        freight_release='Released',
        appointment_date='10-29-2020 13:30~14:30',
        last_free_day='10-28-2020',
        container_spec='Standard 20\' 8\'6\\',
        cy_location='Out-Gated (10/29/2020 14:19)',
        demurrage_due='Paid',
        pay_through_date='10-29-2020',
        tmf=None,
    )
