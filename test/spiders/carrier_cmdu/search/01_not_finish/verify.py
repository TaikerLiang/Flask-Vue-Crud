from typing import List

from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="HO CHI MINH CITY (VN)"),
        pol=LocationItem(name="VUNG TAU (VN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name="CHICAGO, IL (US)"),
        eta="Tuesday 22-FEB-2022 07:00",
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key="CMAU7943654",
        container_no="CMAU7943654",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU7943654",
        local_date_time="Friday 31-Dec-2021 04:46",
        description="Empty to shipper",
        location=LocationItem(name="HO CHI MINH CITY"),
        est_or_actual="A",
        facility="",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CMAU7943654",
        local_date_time="Tuesday 22-Feb-2022 07:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="E",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="HO CHI MINH CITY (VN)"),
        pol=LocationItem(name="VUNG TAU (VN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name="CHICAGO, IL (US)"),
        eta="Tuesday 22-FEB-2022 07:00",
        ata=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="CMAU7943654",
        container_no="CMAU7943654",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU7943654",
        local_date_time="Friday 31-Dec-2021 04:46",
        description="Empty to shipper",
        location=LocationItem(name="HO CHI MINH CITY"),
        est_or_actual="A",
        facility="",
        task_id=1,
    )

    assert results[7] == ContainerStatusItem(
        container_key="CMAU7943654",
        local_date_time="Tuesday 22-Feb-2022 07:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="E",
        facility="",
        task_id=1,
    )
