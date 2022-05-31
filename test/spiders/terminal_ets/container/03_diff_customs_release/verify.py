from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="EITU1162062",
        ready_for_pick_up="No",
        available="No",
        customs_release="Hold",
        appointment_date=None,
        last_free_day=None,
        demurrage=None,
        carrier="EGLV",
        container_spec="40'/Standard/9'6\"",
        holds="Yes",
        cy_location="On Vessel",
        yard_location="On Vessel",
        # extra field name
        service="Local Port/Door Cargo",
        carrier_release="Release",
        tmf="Release",
        demurrage_status=None,
        # not on html
        freight_release="Release",
    )
