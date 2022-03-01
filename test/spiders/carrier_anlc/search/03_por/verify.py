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
        por=LocationItem(name="BANGALORE, KA (IN)"),
        pol=LocationItem(name="CHENNAI (IN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Wednesday 09-FEB-2022 16:04",
    )

    assert results[1] == ContainerItem(
        container_key="CXDU2070501",
        container_no="CXDU2070501",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CXDU2070501",
        local_date_time="Saturday 30-Oct-2021 23:55",
        description="Empty to shipper",
        location=LocationItem(name="HOSUR ICD, TN"),
        est_or_actual="A",
        facility="",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CXDU2070501",
        local_date_time="Monday 06-Dec-2021 19:00",
        description="Discharged in transhipment",
        location=LocationItem(name="PORT KLANG"),
        est_or_actual="A",
        facility="",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="BANGALORE, KA (IN)"),
        pol=LocationItem(name="CHENNAI (IN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Wednesday 09-FEB-2022 16:04",
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="CXDU2070501",
        container_no="CXDU2070501",
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CXDU2070501",
        local_date_time="Saturday 30-Oct-2021 23:55",
        description="Empty to shipper",
        location=LocationItem(name="HOSUR ICD, TN"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )

    assert results[7] == ContainerStatusItem(
        container_key="CXDU2070501",
        local_date_time="Monday 06-Dec-2021 19:00",
        description="Discharged in transhipment",
        location=LocationItem(name="PORT KLANG"),
        est_or_actual="A",
        facility="",
        task_id="1",
    )
