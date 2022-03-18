from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YHU726505",
        por=LocationItem(name="NEW YORK, NY (USNYC)"),
        pol=LocationItem(name="NEW YORK, NY (USNYC)"),
        pod=LocationItem(name="HONGKONG (HKHKG)"),
        place_of_deliv=LocationItem(name="HUANGPU, GUANGZHOU, GD (CNHUA)"),
        etd=None,
        atd="2021/10/25 22:54",
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
        container_key="BSIU9772466",
        container_no="BSIU9772466",
        last_free_day=None,
        task_id=1,
        terminal=LocationItem(name=None),
    )
