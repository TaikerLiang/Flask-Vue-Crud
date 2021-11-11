from typing import Dict

from crawler.core_terminal.items import TerminalItem, InvalidDataFieldItem


def verify(results: Dict):
    assert results["OOLU8981883"] == InvalidDataFieldItem(
        container_no="OOLU8981883", valid_data_dict={"available": ["Yes", "No"]}, invalid_data_dict={"available": "Yo"}
    )
    assert results["CAIU3803055"] == InvalidDataFieldItem(
        container_no="CAIU3803055",
        valid_data_dict={"location": ["C", "V", "Y"], "line_status": ["RELEASE", "HOLD"]},
        invalid_data_dict={"location": "Z", "line_status": "HAHA"},
    )
    assert results["CMAU0101886"] == TerminalItem(
        container_no="CMAU0101886",
        available=False,
        carrier_release=True,
        customs_release=True,
        last_free_day="\xa0",
    )
