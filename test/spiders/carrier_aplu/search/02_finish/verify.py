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
        por=LocationItem(name=None),
        pol=LocationItem(name="SHANGHAI (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Friday 07-JAN-2022 00:26",
    )

    assert results[1] == ContainerItem(
        container_key="TGBU4153370",
        container_no="TGBU4153370",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TGBU4153370",
        local_date_time="Thursday 09-Dec-2021 22:05",
        description="Empty to shipper",
        location=LocationItem(name="SHANGHAI"),
        est_or_actual="A",
        facility="",
    )

    assert results[7] == ContainerStatusItem(
        container_key="TGBU4153370",
        local_date_time="Tuesday 11-Jan-2022 07:09",
        description="Empty in depot",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="A",
        facility="FENIX MARINE TERMINAL",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="SHANGHAI (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Friday 07-JAN-2022 00:26",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="TGBU4153370",
        container_no="TGBU4153370",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="TGBU4153370",
        local_date_time="Thursday 09-Dec-2021 22:05",
        description="Empty to shipper",
        location=LocationItem(name="SHANGHAI"),
        est_or_actual="A",
        facility="",
        task_id=1,
    )

    assert results[7] == ContainerStatusItem(
        container_key="TGBU4153370",
        local_date_time="Tuesday 11-Jan-2022 07:09",
        description="Empty in depot",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="A",
        facility="FENIX MARINE TERMINAL",
        task_id=1,
    )
