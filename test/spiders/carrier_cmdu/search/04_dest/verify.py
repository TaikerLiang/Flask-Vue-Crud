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
        pod=LocationItem(name="NORFOLK, VA (US)"),
        final_dest=LocationItem(name="DETROIT, MI (US)"),
        eta="Wednesday 09-MAR-2022 18:00",
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key="GVTU2455953",
        container_no="GVTU2455953",
    )

    assert results[2] == ContainerStatusItem(
        container_key="GVTU2455953",
        local_date_time="Tuesday 11-Jan-2022 14:29",
        description="In shipper's owned full",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
    )

    assert results[5] == ContainerStatusItem(
        container_key="GVTU2455953",
        local_date_time="Wednesday 09-Mar-2022 18:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="NORFOLK"),
        est_or_actual="E",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (CN)"),
        pod=LocationItem(name="NORFOLK, VA (US)"),
        final_dest=LocationItem(name="DETROIT, MI (US)"),
        place_of_deliv=LocationItem(name="DETROIT, MI (US)"),
        eta="Wednesday 09-MAR-2022 18:00",
        ata=None,
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="GVTU2455953",
        container_no="GVTU2455953",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="GVTU2455953",
        local_date_time="Tuesday 11-Jan-2022 14:29",
        description="In shipper's owned full",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[5] == ContainerStatusItem(
        container_key="GVTU2455953",
        local_date_time="Wednesday 09-Mar-2022 18:00",
        description="Arrival final port of discharge",
        location=LocationItem(name="NORFOLK"),
        est_or_actual="E",
        facility="",
        task_id="1",
    )
