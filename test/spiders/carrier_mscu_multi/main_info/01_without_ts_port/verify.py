from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results):
    assert results[0] == MblItem(
        task_id="1",
        mbl_no="MEDUN4194175",
        pol=LocationItem(name="NINGBO, CN"),
        pod=LocationItem(name="LONG BEACH, US"),
        place_of_deliv=LocationItem(name="LONG BEACH, US"),
        latest_update="09.05.2022 at 10:34 Central Europe Standard Time",
    )

    assert results[1] == ContainerItem(
        task_id="1",
        container_key="GLDU7632978",
        container_no="GLDU7632978",
    )

    assert results[2] == ContainerStatusItem(
        task_id="1",
        container_key="GLDU7632978",
        description="Empty received at CY",
        local_date_time="10/10/2019",
        location=LocationItem(name="LOS ANGELES, US"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[11] == ContainerStatusItem(
        task_id="1",
        container_key="GLDU7632978",
        description="Export at barge yard",
        local_date_time="05/09/2019",
        location=LocationItem(name="ZHAPU, CN"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )
