from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem


def verify(results: List):
    assert results[0] == MblItem(
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
        berthing_time=None,
    )

    assert results[1] == ContainerItem(
        container_key="SEGU5745335",
        container_no="SEGU5745335",
        last_free_day=None,
        task_id=1,
        terminal=LocationItem(name=None),
    )
