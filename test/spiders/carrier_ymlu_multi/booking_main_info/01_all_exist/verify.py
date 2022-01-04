from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YLX391994",
        por=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pol=LocationItem(name="LOS ANGELES, CA (USLAX)"),
        pod=LocationItem(name="KAOHSIUNG (TWKHH)"),
        place_of_deliv=LocationItem(name="MANILA (NORTH HARBOUR) (PHMNN)"),
        etd=None,
        atd="2021/10/23 04:26",
        eta=None,
        ata="2021/11/09 02:44",
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
        berthing_time="2021/11/09 03:40",
    )

    assert results[1] == ContainerItem(
        container_key="SEGU6406167",
        container_no="SEGU6406167",
        last_free_day=None,
        task_id=1,
        terminal=None,
    )
