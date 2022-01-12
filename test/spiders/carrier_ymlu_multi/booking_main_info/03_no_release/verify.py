from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YLX392063",
        por=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pol=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pod=LocationItem(name="PUSAN (KRPUS)"),
        place_of_deliv=LocationItem(name="PUSAN (KRPUS)"),
        etd=None,
        atd="2021/10/31 04:10",
        eta="2021/11/15 15:00",
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
        berthing_time="2021/11/15 17:00",
    )

    assert results[1] == ContainerItem(
        container_key="BMOU5686702",
        container_no="BMOU5686702",
        last_free_day=None,
        task_id=1,
        terminal=LocationItem(name=None),
    )
