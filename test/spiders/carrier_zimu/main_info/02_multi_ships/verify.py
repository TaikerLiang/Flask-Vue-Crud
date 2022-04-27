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
        vessel="ZIM NEW YORK",
        voyage="78",
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="HAIFA, ISRAEL"),
        etd="12-Nov-2018",
        eta="04-Dec-2018",
    )

    assert results[1] == VesselItem(
        vessel_key=1,
        vessel="ASIATIC KING",
        voyage="215",
        pol=LocationItem(name="HAIFA, ISRAEL"),
        pod=LocationItem(name="KOPER, SLOVENIA"),
        etd="06-Dec-2018",
        eta="11-Dec-2018",
    )

    assert results[4] == VesselItem(
        vessel_key=4,
        vessel="RS MISTRAL",
        voyage="4",
        pol=LocationItem(name="PIRAEUS, GREECE"),
        pod=LocationItem(name="DURRES, ALBANIA"),
        etd="03-Jan-2019",
        eta=None,
    )

    assert results[5] == MblItem(
        mbl_no="ZIMUNGB9355973",
        vessel="RS MISTRAL",
        voyage="4",
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="DURRES, ALBANIA"),
        place_of_deliv=LocationItem(un_lo_code=None, name=None),
        etd="12-Nov-2018",
        eta=None,
        deliv_eta=None,
        deliv_ata=None,
    )

    assert results[6] == ContainerItem(
        container_key="TEMU2114116",
        container_no="TEMU2114116",
        terminal_pod=LocationItem(name=None),
    )

    assert results[7] == ContainerStatusItem(
        container_key="TEMU2114116",
        description="Empty container returned from Customer",
        local_date_time="14-Jan-2019 10:25",
        location=LocationItem(name="DURRES, ALBANIA"),
    )
