from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YHU734257",
        por=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pol=LocationItem(name="CHARLESTON, SC (USCHS)"),
        pod=LocationItem(name="KAOHSIUNG (TWKHH)"),
        place_of_deliv=LocationItem(name="TAOYUAN (TWTAO)"),
        etd=None,
        atd="2021/10/11 20:39",
        eta="2021/11/20 03:00",
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="FSCU8038064",
        container_no="FSCU8038064",
        last_free_day=None,
        task_id=1,
    )

    assert results[5] == ContainerItem(
        container_key="TEMU8505289",
        container_no="TEMU8505289",
        last_free_day=None,
        task_id=1,
    )
