from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


def verify(results: List):
    assert results[1] == MblItem(
        booking_no="YHU739759",
        por=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pol=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pod=LocationItem(name="TAN CANG - CAI MEP TERMINAL (VNTCT)"),
        place_of_deliv=LocationItem(name="BINH DUONG PORT (VNBDU)"),
        etd=None,
        atd="2021/10/11 20:39",
        eta=None,
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
    )

    assert results[2] == ContainerItem(
        container_key="SEGU5745335",
        container_no="SEGU5745335",
        last_free_day=None,
        task_id=1,
    )
