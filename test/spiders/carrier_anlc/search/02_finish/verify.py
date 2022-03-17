from typing import List

from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
)


def verify(results: List):
    results.pop(0)

    assert results[0] == ContainerItem(
        container_key="CMAU0720010",
        container_no="CMAU0720010",
    )

    assert results[1] == ContainerStatusItem(
        container_key="CMAU0720010",
        local_date_time="Wednesday 27-Oct-2021 13:14",
        description="Empty to shipper",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="A",
        facility="",
    )

    assert results[4] == ContainerStatusItem(
        container_key="CMAU0720010",
        local_date_time="Thursday 20-Jan-2022 19:09",
        description="Discharged",
        location=LocationItem(name="LONG BEACH, CA"),
        est_or_actual="A",
        facility="SSA - LGB PIER A",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == ContainerItem(
        container_key="CMAU0720010",
        container_no="CMAU0720010",
        task_id="1",
    )

    assert results[1] == ContainerStatusItem(
        container_key="CMAU0720010",
        local_date_time="Wednesday 27-Oct-2021 13:14",
        description="Empty to shipper",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[4] == ContainerStatusItem(
        container_key="CMAU0720010",
        local_date_time="Thursday 20-Jan-2022 19:09",
        description="Discharged",
        location=LocationItem(name="LONG BEACH, CA"),
        est_or_actual="A",
        facility="SSA - LGB PIER A",
        task_id="1",
    )
