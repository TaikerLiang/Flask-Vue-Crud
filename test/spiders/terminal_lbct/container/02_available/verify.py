from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='TGBU8679362',
        freight_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='11/15/2020 14:33 (Actual)',
        ready_for_pick_up='YES',
        appointment_date='11-19-2020 14:00',
        last_free_day='11/19/2020',
        carrier='OOL',
        container_spec='40HQ',
        cy_location='GROUNDED',
        vessel='SINGAPORE 139',
        voyage='139',
        # on html
        # field same like other terminal
        tmf='RELEASED',
        # new field
        owed='$0',
        full_empty='Full',
    )
