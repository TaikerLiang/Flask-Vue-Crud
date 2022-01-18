from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="FREMANTLE (AU)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sat 16 Nov 2019 19:58",
    )

    assert results[1] == ContainerItem(
        container_key="TCLU7712319",
        container_no="TCLU7712319",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TCLU7712319",
        local_date_time="Tue 22 Oct 2019 17:35",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        facility="",
        est_or_actual="A",
    )

    assert results[7] == ContainerStatusItem(
        container_key="TCLU7712319",
        local_date_time="Sat 16 Nov 2019 19:58",
        description="Discharged",
        location=LocationItem(name="FREMANTLE"),
        facility="",
        est_or_actual="A",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="KAOHSIUNG (TW)"),
        pod=LocationItem(name="FREMANTLE (AU)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Sat 16 Nov 2019 19:58",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="TCLU7712319",
        container_no="TCLU7712319",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="TCLU7712319",
        local_date_time="Tue 22 Oct 2019 17:35",
        description="Empty to shipper",
        location=LocationItem(name="KAOHSIUNG"),
        facility="",
        est_or_actual="A",
        task_id=1,
    )

    assert results[7] == ContainerStatusItem(
        container_key="TCLU7712319",
        local_date_time="Sat 16 Nov 2019 19:58",
        description="Discharged",
        location=LocationItem(name="FREMANTLE"),
        facility="",
        est_or_actual="A",
        task_id=1,
    )
