from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='CSLU6209412',
        freight_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='',
        ready_for_pick_up='NO (NOT DISCHARGED)',
        appointment_date=None,
        last_free_day='',
        carrier='OOL',
        container_spec='40HQ',
        cy_location='ON VESSEL',
        vessel='OOCL TAIPEI 047',
        voyage='047',
        # on html
        # field same like other terminal
        tmf='ACTIVE',
        # new field
        owed='',
        full_empty='Full',
    )
