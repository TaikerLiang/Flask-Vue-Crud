from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
    VesselItem,
)


def verify(results):
    assert results[0] == VesselItem(
        vessel_key=0,
        vessel="SEAMAX NEW HAVEN",
        voyage="3",
        pol=LocationItem(name="SAVANNAH (GA), U.S.A."),
        pod=LocationItem(name="KAOHSIUNG, TAIWAN"),
        etd="28-Nov-2019",
        eta="08-Jan-2020",
    )

    assert results[1] == MblItem(
        mbl_no="ZIMULAX0140902",
        vessel="SEAMAX NEW HAVEN",
        voyage="3",
        por=LocationItem(name="HUNTSVILLE (AL), U.S.A."),
        pol=LocationItem(name="SAVANNAH (GA), U.S.A."),
        pod=LocationItem(name="KAOHSIUNG, TAIWAN"),
        place_of_deliv=LocationItem(un_lo_code=None, name=None),
        etd="28-Nov-2019",
        eta="08-Jan-2020",
        deliv_eta=None,
        deliv_ata=None,
    )

    assert results[2] == ContainerItem(
        container_key="GAOU6141898",
        container_no="GAOU6141898",
        terminal_pod=LocationItem(name=None),
    )

    assert results[3] == ContainerStatusItem(
        container_key="GAOU6141898",
        description="Vessel departure from Port of Loading to Port of Discharge",
        local_date_time="29-Nov-2019 03:15",
        location=LocationItem(name="SAVANNAH (GA), U.S.A."),
    )
