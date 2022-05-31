from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="TCNU3577497",
        carrier_release="RELEASED",
        customs_release="ACTIVE",
        discharge_date="08/18/2021 01:32 (Actual)",
        ready_for_pick_up="NO (HOLD)",
        available="NO (HOLD)",
        appointment_date=None,
        gate_out_date="",
        last_free_day="8/23/2021",
        carrier="COS",
        container_spec="40HQ",
        cy_location="GROUNDED",
        yard_location="GROUNDED",
        vessel="COSCO SHIPPING ANDES 018",
        voyage="018",
        # on html
        # field same like other terminal
        tmf="RELEASED",
        # new field
        owed="$0",
        full_empty="Full",
    )
