from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='CAAU5077128',
        carrier='MSCU',
        ready_for_pick_up='Delivered',
        customs_release='Released',
        freight_release='Released',
        appointment_date='10-22-2020 15:00~16:00',
        last_free_day='10-22-2020',
        container_spec='Standard 40\' 9\'6\\',
        cy_location='Out-Gated (10/22/2020 18:53)',
        demurrage_due=None,
        pay_through_date=None,
        tmf=None,
    )
