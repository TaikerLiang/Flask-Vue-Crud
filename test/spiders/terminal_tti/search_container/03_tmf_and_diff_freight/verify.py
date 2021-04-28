from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='HASU4204375',
        carrier='SUDU',
        ready_for_pick_up='No',
        customs_release='Released',
        freight_release='No Entry',
        appointment_date='Not Ready for Appt',
        last_free_day=None,
        container_spec='Standard 40\' 9\'6\\',
        cy_location='On Ship',

        demurrage_due=None,
        pay_through_date=None,
        tmf='Released',
    )

