from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YHU731790",
        por=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pol=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pod=LocationItem(name="TAN CANG - CAI MEP TERMINAL (VNTCT)"),
        place_of_deliv=LocationItem(name="BINH DUONG PORT (VNBDU)"),
        etd=None,
        atd="2021/10/20 12:54",
        eta=None,
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
        berthing_time=None,
        vessel="MADRID BRIDGE",
        voyage="015W (EC4132W)",
    )

    assert results[1] == ContainerItem(
        container_key="BMOU5687951",
        container_no="BMOU5687951",
        last_free_day=None,
        task_id=1,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[2], RequestOption)

    assert results[3] == ContainerItem(
        container_key="BMOU5757067",
        container_no="BMOU5757067",
        last_free_day=None,
        task_id=1,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[4], RequestOption)

    # More containers and their requests
