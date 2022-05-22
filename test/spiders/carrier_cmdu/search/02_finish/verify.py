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
        pol=LocationItem(name="SHANGHAI (CN)"),
        pod=LocationItem(name="NEW YORK, NY (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sunday 30-JAN-2022 22:35",
    )

    assert results[1] == ContainerItem(
        container_key="CMAU4128458",
        container_no="CMAU4128458",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU4128458",
        local_date_time="Wednesday 01-Dec-2021 13:22",
        description="Empty to shipper",
        location=LocationItem(name="SHANGHAI"),
        est_or_actual="A",
        facility="",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CMAU4128458",
        local_date_time="Friday 04-Feb-2022 12:29",
        description="Empty in depot",
        location=LocationItem(name="NEW YORK, NY"),
        est_or_actual="A",
        facility="APM ELIZABETH NJ",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="SHANGHAI (CN)"),
        pod=LocationItem(name="NEW YORK, NY (US)"),
        place_of_deliv=LocationItem(name=None),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sunday 30-JAN-2022 22:35",
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="CMAU4128458",
        container_no="CMAU4128458",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU4128458",
        local_date_time="Wednesday 01-Dec-2021 13:22",
        description="Empty to shipper",
        location=LocationItem(name="SHANGHAI"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CMAU4128458",
        local_date_time="Friday 04-Feb-2022 12:29",
        description="Empty in depot",
        location=LocationItem(name="NEW YORK, NY"),
        est_or_actual="A",
        facility="APM ELIZABETH NJ",
        task_id="1",
    )
