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
        vessel="CAPE TAINARO",
        voyage="3",
        pol=LocationItem(name="SHANGHAI (SH), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="WILMINGTON (NC), U.S.A."),
        etd="17-Oct-2019",
        eta="18-Nov-2019",
    )

    assert results[1] == MblItem(
        mbl_no="ZIMUSNH1105927",
        vessel="CAPE TAINARO",
        voyage="3",
        por=LocationItem(name=None),
        pol=LocationItem(name="SHANGHAI (SH), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="WILMINGTON (NC), U.S.A."),
        place_of_deliv=LocationItem(un_lo_code=None, name="CHARLOTTE (NC), U.S.A."),
        etd="17-Oct-2019",
        eta="18-Nov-2019",
        deliv_eta="27-Nov-2019",
    )

    assert results[2] == ContainerItem(
        container_key="ZCSU8513632",
        container_no="ZCSU8513632",
    )

    assert results[3] == ContainerStatusItem(
        container_key="ZCSU8513632",
        description="Container is available to be released / delivered",
        local_date_time="22-Nov-2019 19:18",
        location=LocationItem(name="CHARLOTTE (NC), U.S.A."),
    )
