from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="CMAU8656108",
        customs_release="RELEASED",
        freight_release="RELEASED",
        demurrage=None,
        gate_out_date="2022-02-26T15:32:00",
        last_free_day=None,
        carrier="CMDU",
        container_spec="40HC",
        vessel="CMA CGM MAGELLAN",
        voyage="MAGE-0MBAEW1",
    )
    assert results[1] == TerminalItem(
        container_no="TRHU3021789",
        customs_release="RELEASED",
        freight_release="RELEASED",
        demurrage="250.00",
        gate_out_date="2022-03-12T14:38:00",
        last_free_day="3/11/2022 11:59:00 PM",
        carrier="ONEY",
        container_spec=None,
        vessel="AL QIBLA",
        voyage="ALQI-024W",
    )
    assert results[2] == TerminalItem(
        container_no="TGHU6953748",
        customs_release="RELEASED",
        freight_release=None,
        demurrage=None,
        gate_out_date=None,
        last_free_day=None,
        carrier="ZIMU",
        container_spec="40HC",
        vessel="MSC ELMA",
        voyage="ELMA-UL211W",
    )
