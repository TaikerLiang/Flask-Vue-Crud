from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="WHLU0343058",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="08/06/2021 23:38 (Actual)",
        ready_for_pick_up="YES",
        available="YES",
        appointment_date=None,
        gate_out_date="",
        last_free_day="8/18/2021",
        carrier="WHL",
        container_spec="20GP",
        cy_location="GROUNDED",
        yard_location="GROUNDED",
        vessel="HOPE ISLAND 005",
        voyage="005",
        # on html
        # field same like other terminal
        tmf="RELEASED",
        # new field
        owed="$0",
        full_empty="Full",
    )
