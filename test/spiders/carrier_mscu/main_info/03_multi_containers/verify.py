from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results):
    assert results[0] == ContainerItem(
        container_key="MEDU4550625",
        container_no="MEDU4550625",
    )

    assert results[1] == ContainerStatusItem(
        container_key="MEDU4550625",
        description="Empty received at CY",
        local_date_time="24/10/2019",
        location=LocationItem(name="LONG BEACH, US"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[12] == ContainerItem(
        container_key="GLDU7636572",
        container_no="GLDU7636572",
    )

    assert results[13] == ContainerStatusItem(
        container_key="GLDU7636572",
        description="Empty received at CY",
        local_date_time="23/10/2019",
        location=LocationItem(name="LONG BEACH, US"),
        vessel=None,
        voyage=None,
        est_or_actual="A",
    )

    assert results[24] == ContainerItem(
        container_key="TGCU0233249",
        container_no="TGCU0233249",
    )

    assert results[-1] == MblItem(
        mbl_no="MEDUMY898253",
        pol=LocationItem(name="TANJUNG PELEPAS, MY"),
        pod=LocationItem(name="LOS ANGELES, US"),
        etd="17/09/2019",
        eta=None,
        vessel="GUDRUN MAERSK",
        place_of_deliv=LocationItem(name="LOS ANGELES, US"),
        latest_update="05.11.2021 at 03:30 Central Europe Standard Time",
    )
