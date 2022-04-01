from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="MAGU5304736",
        customs_release="RELEASED",
        freight_release="RELEASED",
        demurrage=None,
        gate_out_date=None,
        last_free_day=None,
        carrier="WHLC",
        container_spec="40HQ",
        vessel=None,
        voyage=None,
    )
    assert results[1] == TerminalItem(
        container_no="MSDU8213580",
        customs_release="RELEASED",
        freight_release="RELEASED",
        demurrage=None,
        gate_out_date=None,
        last_free_day=None,
        carrier="MSCU",
        container_spec="40HC",
        vessel=None,
        voyage=None,
    )
    assert results[2] == TerminalItem(
        container_no="TCKU7313610",
        customs_release=None,
        freight_release=None,
        demurrage=None,
        gate_out_date="2021-07-15T00:27:08",
        last_free_day="6/10/2021 11:59:00 PM",
        carrier="WHLC",
        container_spec="40DH",
        vessel=None,
        voyage="196E",
    )
