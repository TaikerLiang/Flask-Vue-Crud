from typing import List

from crawler.core_carrier.items import ExportErrorData, MblItem, LocationItem, ContainerItem
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR


def verify(results: List):
    assert results[0] == ExportErrorData(
        task_id=1, booking_no="YHU731790", detail="Firms code parsing error", status=CARRIER_RESULT_STATUS_ERROR
    )

    assert results[1] == MblItem(
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
    )

    assert results[2] == ContainerItem(
        container_key="BMOU5687951",
        container_no="BMOU5687951",
        last_free_day=None,
        task_id=1,
        terminal=None,
    )

    assert results[6] == ContainerItem(
        container_key="CAIU4283277",
        container_no="CAIU4283277",
        last_free_day=None,
        task_id=1,
        terminal=None,
    )
