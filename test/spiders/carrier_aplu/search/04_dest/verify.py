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
        pol=LocationItem(name="YANTIAN (CN)"),
        pod=LocationItem(name="OAKLAND, CA (US)"),
        final_dest=LocationItem(name="CHICAGO, IL (US)"),
        eta=None,
        ata="Thursday 03-FEB-2022 15:57",
    )

    assert results[1] == ContainerItem(
        container_key="TLLU4400681",
        container_no="TLLU4400681",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TLLU4400681",
        local_date_time="Friday 24-Dec-2021 04:03",
        description="Empty to shipper",
        location=LocationItem(name="YANTIAN"),
        est_or_actual="A",
        facility="",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TLLU4400681",
        local_date_time="Thursday 03-Feb-2022 15:57",
        description="Discharged",
        location=LocationItem(name="OAKLAND, CA"),
        est_or_actual="A",
        facility="SSA BERTH 58 EAST GATE",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="YANTIAN (CN)"),
        pod=LocationItem(name="OAKLAND, CA (US)"),
        final_dest=LocationItem(name="CHICAGO, IL (US)"),
        place_of_deliv=LocationItem(name="CHICAGO, IL (US)"),
        eta=None,
        ata="Thursday 03-FEB-2022 15:57",
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="TLLU4400681",
        container_no="TLLU4400681",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TLLU4400681",
        local_date_time="Friday 24-Dec-2021 04:03",
        description="Empty to shipper",
        location=LocationItem(name="YANTIAN"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TLLU4400681",
        local_date_time="Thursday 03-Feb-2022 15:57",
        description="Discharged",
        location=LocationItem(name="OAKLAND, CA"),
        est_or_actual="A",
        facility="SSA BERTH 58 EAST GATE",
        task_id="1",
    )
