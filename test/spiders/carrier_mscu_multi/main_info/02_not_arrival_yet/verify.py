from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results):
    assert results[0] == MblItem(
        task_id="1",
        mbl_no="MEDUNG283959",
        pol=LocationItem(name="NINGBO, CN"),
        pod=LocationItem(name="SUAPE, BR"),
        place_of_deliv=LocationItem(name=None),
        latest_update="09.05.2022 at 10:36 Central Europe Standard Time",
    )

    assert results[1] == ContainerItem(
        task_id="1",
        container_key="FSCU4872850",
        container_no="FSCU4872850",
    )

    assert results[2] == ContainerStatusItem(
        task_id="1",
        container_key="FSCU4872850",
        description="Empty received at CY",
        local_date_time="30/04/2020",
        location=LocationItem(name="IPOJUCA, BR"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[5] == ContainerStatusItem(
        task_id="1",
        container_key="FSCU4872850",
        description="Full Transshipment Loaded",
        local_date_time="08/04/2020",
        location=LocationItem(name="GIOIA TAURO, IT"),
        vessel="MSC JEONGMIN",
        voyage="Voyage MM014A",
        est_or_actual="A",
    )
