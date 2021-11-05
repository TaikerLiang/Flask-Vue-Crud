from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="FSCU4872850",
        container_no="FSCU4872850",
    )

    assert results[1] == ContainerStatusItem(
        container_key="FSCU4872850",
        description="Empty received at CY",
        local_date_time="30/04/2020",
        location=LocationItem(name="IPOJUCA, BR"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[4] == ContainerStatusItem(
        container_key="FSCU4872850",
        description="Full Transshipment Loaded",
        local_date_time="08/04/2020",
        location=LocationItem(name="GIOIA TAURO, IT"),
        vessel="MSC JEONGMIN",
        voyage="MM014A",
        est_or_actual="A",
    )

    assert results[-1] == MblItem(
        mbl_no="MEDUNG283959",
        pol=LocationItem(name="NINGBO, CN"),
        pod=LocationItem(name="SUAPE, BR"),
        etd="26/02/2020",
        vessel="MSC JADE",
        place_of_deliv=LocationItem(name="SUAPE, BR"),
        latest_update="05.11.2021 at 03:30 Central Europe Standard Time",
    )
