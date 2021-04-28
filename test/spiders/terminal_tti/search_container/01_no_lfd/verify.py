from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='MSDU7965509',
        carrier='MSCU',
        ready_for_pick_up=None,
        customs_release='Missing',
        freight_release='Missing',
        appointment_date='Not an Import Container',
        last_free_day=None,
        container_spec='Standard 40\' 9\'6\\',
        cy_location='Out-Gated (10/22/2020 15:08)',

        demurrage_due=None,
        pay_through_date=None,
        tmf=None,
    )


