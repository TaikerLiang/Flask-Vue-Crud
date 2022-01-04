from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YLX392742",
        por=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pol=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pod=LocationItem(name="NINGBO, ZJ (CNNGB)"),
        place_of_deliv=LocationItem(name="HAIPHONG (VNHPH)"),
        etd=None,
        atd="2021/10/29 19:00",
        eta="2021/11/15 08:00",
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
        berthing_time="2021/11/15 10:00",
    )

    assert results[1] == ContainerItem(
        container_key="TTNU1129599",
        container_no="TTNU1129599",
        last_free_day=None,
        task_id=1,
        terminal=None,
    )
