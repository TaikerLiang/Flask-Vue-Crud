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
        vessel="MSC LA SPEZIA",
        voyage="4",
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="PIRAEUS, GREECE"),
        etd="17-Oct-2019",
        eta="17-Nov-2019",
    )

    assert results[1] == MblItem(
        mbl_no="ZIMUNGB9490976",
        vessel=None,
        voyage=None,
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="DURRES, ALBANIA"),
        place_of_deliv=LocationItem(un_lo_code=None, name=None),
        final_dest=LocationItem(un_lo_code=None, name=None),
        etd="17-Oct-2019",
        eta="22-Nov-2019",
        deliv_eta=None,
        deliv_ata=None,
    )

    assert results[2] == ContainerItem(
        container_key="TRHU2925251",
        container_no="TRHU2925251",
        terminal_pod=LocationItem(name=None),
    )

    assert results[3] == ContainerStatusItem(
        container_key="TRHU2925251",
        description="Vessel departure from Port of Loading to Transshipment Port",
        local_date_time="17-Oct-2019 15:25",
        location=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
    )
