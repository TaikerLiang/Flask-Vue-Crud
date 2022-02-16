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
        por=LocationItem(name="TAICHUNG (TW)"),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="LONG BEACH, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sunday 16-JAN-2022 21:40",
    )

    assert results[1] == ContainerItem(
        container_key="CAIU3813177",
        container_no="CAIU3813177",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CAIU3813177",
        local_date_time="Thursday 16-Dec-2021 08:10",
        description="Empty to shipper",
        location=LocationItem(name="TAICHUNG"),
        est_or_actual="A",
        facility="",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CAIU3813177",
        local_date_time="Sunday 16-Jan-2022 21:40",
        description="Discharged",
        location=LocationItem(name="LONG BEACH, CA"),
        est_or_actual="A",
        facility="LONG BEACH CONTAINER TERM",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="TAICHUNG (TW)"),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="LONG BEACH, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sunday 16-JAN-2022 21:40",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="CAIU3813177",
        container_no="CAIU3813177",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="CAIU3813177",
        local_date_time="Thursday 16-Dec-2021 08:10",
        description="Empty to shipper",
        location=LocationItem(name="TAICHUNG"),
        est_or_actual="A",
        facility="",
        task_id=1,
    )

    assert results[7] == ContainerStatusItem(
        container_key="CAIU3813177",
        local_date_time="Sunday 16-Jan-2022 21:40",
        description="Discharged",
        location=LocationItem(name="LONG BEACH, CA"),
        est_or_actual="A",
        facility="LONG BEACH CONTAINER TERM",
        task_id=1,
    )
