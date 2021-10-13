from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        available="NOT AVAILABLE",
        container_no="TCLU7732296",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day="2021-09-24T00:00:00",
        vessel="MSC TIANJIN",
        voyage="131A",
    )
    assert results[1] == TerminalItem(
        available="LOADED ON VESSEL",
        container_no="YMMU1023477",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day="2021-09-22T00:00:00",
        vessel="ONE HOUSTON",
        voyage="046E",
    )
    assert results[2] == TerminalItem(
        available="NOT AVAILABLE",
        container_no="SEGU4568364",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day="0001-01-01T00:00:00",
        vessel="ONE HAWK",
        voyage="020E",
    )
