from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
    VesselItem,
)


def verify(results):
    assert results[0] == VesselItem(
        vessel_key=0,
        vessel="ANNA MAERSK",
        voyage="5",
        pol=LocationItem(name="SEATTLE (WA), U.S.A."),
        pod=LocationItem(name="KAOHSIUNG, TAIWAN"),
        etd="12-Oct-2019",
        eta="03-Nov-2019",
    )

    assert results[1] == MblItem(
        mbl_no="ZIMULAX0139127",
        vessel="ANNA MAERSK",
        voyage="5",
        por=LocationItem(name=None),
        pol=LocationItem(name="SEATTLE (WA), U.S.A."),
        pod=LocationItem(name="KAOHSIUNG, TAIWAN"),
        place_of_deliv=LocationItem(un_lo_code=None, name=None),
        etd="12-Oct-2019",
        eta="03-Nov-2019",
        deliv_eta=None,
        deliv_ata=None,
    )

    assert results[2] == ContainerItem(
        container_key="SZLU9062541",
        container_no="SZLU9062541",
        terminal_pod=LocationItem(name=None),
    )

    assert results[3] == ContainerStatusItem(
        container_key="SZLU9062541",
        description="Container was discharged at Port of Destination",
        local_date_time="03-Nov-2019 06:52",
        location=LocationItem(name="KAOHSIUNG, TAIWAN"),
    )
