from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
    VesselItem,
)


def verify(results):
    assert results[0] == VesselItem(
        task_id="1",
        vessel_key=0,
        vessel="MSC LA SPEZIA",
        voyage="4",
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="PIRAEUS, GREECE"),
        etd="17-Oct-2019",
        eta="17-Nov-2019",
    )

    assert results[1] == MblItem(
        task_id="1",
        mbl_no="ZIMUNGB9490976",
        vessel=None,
        voyage=None,
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="DURRES, ALBANIA"),
        place_of_deliv=LocationItem(un_lo_code=None, name=None),
        etd="17-Oct-2019",
        eta="22-Nov-2019",
        deliv_eta=None,
        deliv_ata=None,
    )

    assert results[2] == ContainerItem(
        task_id="1",
        container_key="TRHU2925251",
        container_no="TRHU2925251",
        terminal_pod=LocationItem(name=None),
    )

    assert results[3] == ContainerStatusItem(
        task_id="1",
        container_key="TRHU2925251",
        description="Vessel departure from Port of Loading to Transshipment Port",
        local_date_time="17-Oct-2019 15:25",
        location=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
    )
