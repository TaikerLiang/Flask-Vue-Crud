from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List[TerminalItem]):
    assert results[0] == TerminalItem(
        available="Not Available",
        container_no="KOCU4002224",
        carrier="Hyundai America Shipping(HDMU)",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        holds="LINE HOLD-UNIT",
        container_spec="40GP96",
        weight="12200.0 KG",
    )
