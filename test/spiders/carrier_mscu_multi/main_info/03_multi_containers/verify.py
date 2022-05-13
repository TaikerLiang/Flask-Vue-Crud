from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results):
    assert results[0] == MblItem(
        task_id="1",
        mbl_no="MEDUMY898253",
        pol=LocationItem(name="TANJUNG PELEPAS, MY"),
        pod=LocationItem(name="LOS ANGELES, US"),
        place_of_deliv=LocationItem(name=None),
        latest_update="09.05.2022 at 10:37 Central Europe Standard Time",
    )

    assert results[1] == ContainerItem(
        task_id="1",
        container_key="GLDU7636572",
        container_no="GLDU7636572",
    )

    assert results[2] == ContainerStatusItem(
        task_id="1",
        container_key="GLDU7636572",
        description="Empty received at CY",
        local_date_time="23/10/2019",
        location=LocationItem(name="LONG BEACH, US"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[13] == ContainerItem(
        task_id="1",
        container_key="TGCU0233249",
        container_no="TGCU0233249",
    )

    assert results[14] == ContainerStatusItem(
        task_id="1",
        container_key="TGCU0233249",
        description="Empty received at CY",
        local_date_time="23/10/2019",
        location=LocationItem(name="LONG BEACH, US"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[25] == ContainerItem(
        task_id="1",
        container_key="MEDU4550625",
        container_no="MEDU4550625",
    )
