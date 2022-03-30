from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
)


def verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="QINGDAO (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name="ST LOUIS, MO (US)"),
        eta=None,
        ata="Saturday 18-DEC-2021 16:17",
    )

    assert results[1] == ContainerItem(
        container_key="APZU4632334",
        container_no="APZU4632334",
    )

    assert results[2] == ContainerStatusItem(
        container_key="APZU4632334",
        local_date_time="Monday 15-Nov-2021 17:53",
        description="Empty to shipper",
        location=LocationItem(name="QINGDAO"),
        est_or_actual="A",
        facility="",
    )

    assert results[10] == ContainerStatusItem(
        container_key="APZU4632334",
        local_date_time="Monday 27-Dec-2021 09:24",
        description="Container on rail for import",
        location=LocationItem(name="GORHAM, IL"),
        est_or_actual="A",
        facility="GORHAM, IL - PASS THRU",
    )


def multi_verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="QINGDAO (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        place_of_deliv=LocationItem(name="ST LOUIS, MO (US)"),
        final_dest=LocationItem(name="ST LOUIS, MO (US)"),
        eta=None,
        ata="Saturday 18-DEC-2021 16:17",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="APZU4632334",
        container_no="APZU4632334",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="APZU4632334",
        local_date_time="Monday 15-Nov-2021 17:53",
        description="Empty to shipper",
        location=LocationItem(name="QINGDAO"),
        est_or_actual="A",
        facility="",
        task_id=1,
    )

    assert results[10] == ContainerStatusItem(
        container_key="APZU4632334",
        local_date_time="Monday 27-Dec-2021 09:24",
        description="Container on rail for import",
        location=LocationItem(name="GORHAM, IL"),
        est_or_actual="A",
        facility="GORHAM, IL - PASS THRU",
        task_id=1,
    )
