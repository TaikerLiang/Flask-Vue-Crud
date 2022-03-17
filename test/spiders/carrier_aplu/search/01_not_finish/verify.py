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
        pol=LocationItem(name="NINGBO (CN)"),
        pod=LocationItem(name="MIAMI, FL (US)"),
        final_dest=LocationItem(name=None),
        eta="Sunday 20-FEB-2022 20:00",
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key="TDRU4118210",
        container_no="TDRU4118210",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TDRU4118210",
        local_date_time="Sunday 26-Dec-2021 15:01",
        description="In shipper's owned full",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TDRU4118210",
        local_date_time="Sunday 20-Feb-2022 20:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MIAMI"),
        est_or_actual="E",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (CN)"),
        pod=LocationItem(name="MIAMI, FL (US)"),
        final_dest=LocationItem(name=None),
        eta="Sunday 20-FEB-2022 20:00",
        ata=None,
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="TDRU4118210",
        container_no="TDRU4118210",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TDRU4118210",
        local_date_time="Sunday 26-Dec-2021 15:01",
        description="In shipper's owned full",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TDRU4118210",
        local_date_time="Sunday 20-Feb-2022 20:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="MIAMI"),
        est_or_actual="E",
        facility="",
        task_id="1",
    )
