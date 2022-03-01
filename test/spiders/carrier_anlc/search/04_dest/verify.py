from typing import List

from crawler.core_carrier.items import ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == ContainerItem(
        container_key="TCLU7703472",
        container_no="TCLU7703472",
    )

    assert results[1] == ContainerStatusItem(
        container_key="TCLU7703472",
        local_date_time="Tuesday 18-Jan-2022 15:58",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        est_or_actual="A",
        facility="",
    )

    assert results[4] == ContainerStatusItem(
        container_key="TCLU7703472",
        local_date_time="Thursday 17-Feb-2022 06:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="E",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == ContainerItem(
        container_key="TCLU7703472",
        container_no="TCLU7703472",
        task_id="1",
    )

    assert results[1] == ContainerStatusItem(
        container_key="TCLU7703472",
        local_date_time="Tuesday 18-Jan-2022 15:58",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[4] == ContainerStatusItem(
        container_key="TCLU7703472",
        local_date_time="Thursday 17-Feb-2022 06:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="E",
        facility="",
        task_id="1",
    )
