from typing import Dict

from crawler.core_terminal.items import TerminalItem


def verify(results: Dict):
    assert results["OOLU8981883"] == TerminalItem(
        container_no="OOLU8981883",
        available=True,
        carrier_release=True,
        customs_release=True,
        last_free_day="\xa0",
    )
    assert results["FCIU6164362"] == TerminalItem(
        container_no="FCIU6164362",
        available=False,
        carrier_release=False,
        customs_release=False,
        last_free_day="\xa0",
    )
    assert results["TRLU8224030"] == TerminalItem(
        container_no="TRLU8224030",
        available=False,
        carrier_release=True,
        customs_release=True,
        last_free_day="\xa0",
    )
    assert results["CAIU3803055"] == TerminalItem(
        container_no="CAIU3803055",
        available=False,
        carrier_release=False,
        customs_release=True,
        last_free_day="\xa0",
    )
    assert results["CMAU0101886"] == TerminalItem(
        container_no="CMAU0101886",
        available=False,
        carrier_release=True,
        customs_release=True,
        last_free_day="\xa0",
    )
