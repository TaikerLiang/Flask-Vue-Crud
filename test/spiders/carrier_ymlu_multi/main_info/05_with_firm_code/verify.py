from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no="W226020752",
        por=LocationItem(name="YANTIAN, GD, China"),
        pol=LocationItem(name="YANTIAN, GD, China"),
        pod=LocationItem(name="LOS ANGELES, CA, USA"),
        place_of_deliv=LocationItem(name="LOS ANGELES, CA, USA"),
        etd=None,
        atd="2020/03/19 16:25",
        eta="2020/04/05 14:30",
        ata=None,
        firms_code="Y258",
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status="(not yet Customs Release)",
        customs_release_date=None,
        task_id=1,
        berthing_time="2020/04/05 17:00",
        vessel="ONE ARCADIA",
        voyage="048E (PS7011E)",
    )

    assert results[1] == ContainerItem(
        container_key="YMLU8604968",
        container_no="YMLU8604968",
        last_free_day=None,
        task_id=1,
        terminal_pod=LocationItem(name="Y258"),
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        "https://www.yangming.com/e-service/Track_Trace/"
        "ctconnect.aspx?rdolType=BL&ctnrno=YMLU8604968&blno=W226020752&movertype=11&lifecycle=1"
    )

    assert results[3] == ContainerItem(
        container_key="BEAU4528734",
        container_no="BEAU4528734",
        last_free_day=None,
        task_id=1,
        terminal_pod=LocationItem(name="Y258"),
    )

    assert isinstance(results[4], RequestOption)
    assert results[4].url == (
        "https://www.yangming.com/e-service/Track_Trace/"
        "ctconnect.aspx?rdolType=BL&ctnrno=BEAU4528734&blno=W226020752&movertype=11&lifecycle=1"
    )
