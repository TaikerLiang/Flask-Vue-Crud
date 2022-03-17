from typing import List

from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="MELBOURNE (AU)"),
        final_dest=LocationItem(name=None),
        eta="Friday 04-MAR-2022 06:00",
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key="TCLU7704930",
        container_no="TCLU7704930",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TCLU7704930",
        local_date_time="Thursday 10-Feb-2022 17:08",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        est_or_actual="A",
        facility="",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TCLU7704930",
        local_date_time="Friday 04-Mar-2022 06:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="E",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="MELBOURNE (AU)"),
        final_dest=LocationItem(name=None),
        eta="Friday 04-MAR-2022 06:00",
        ata=None,
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="TCLU7704930",
        container_no="TCLU7704930",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TCLU7704930",
        local_date_time="Thursday 10-Feb-2022 17:08",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TCLU7704930",
        local_date_time="Friday 04-Mar-2022 06:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MELBOURNE"),
        est_or_actual="E",
        facility="",
        task_id="1",
    )
