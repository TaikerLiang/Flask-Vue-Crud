from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="KANSAS CITY, KS (US)"),
        pol=LocationItem(name="LOS ANGELES, CA (US)"),
        pod=LocationItem(name="TAIPEI (TW)"),
        final_dest=LocationItem(name="KEELUNG (TW)"),
        eta=None,
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key="CMAU4352196",
        container_no="CMAU4352196",
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Fri 17 Jan 2020 13:54",
        description="Empty to shipper",
        location=LocationItem(name="SALT LAKE CITY, UT"),
        facility="RSD Container Yard Services",
        est_or_actual="A",
    )

    assert results[6] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Sat 25 Jan 2020 09:00",
        description="Container on rail for export",
        location=LocationItem(name="LOS ANGELES, CA"),
        facility="UP-ICTF",
        est_or_actual="A",
    )

    assert results[10] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Wed 05 Feb 2020 18:22",
        description="Loaded on board",
        location=LocationItem(name="LOS ANGELES, CA"),
        facility="FENIX MARINE TERMINAL",
        est_or_actual="A",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name="KANSAS CITY, KS (US)"),
        pol=LocationItem(name="LOS ANGELES, CA (US)"),
        pod=LocationItem(name="TAIPEI (TW)"),
        final_dest=LocationItem(name="KEELUNG (TW)"),
        eta=None,
        ata=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="CMAU4352196",
        container_no="CMAU4352196",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Fri 17 Jan 2020 13:54",
        description="Empty to shipper",
        location=LocationItem(name="SALT LAKE CITY, UT"),
        facility="RSD Container Yard Services",
        est_or_actual="A",
        task_id=1,
    )

    assert results[6] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Sat 25 Jan 2020 09:00",
        description="Container on rail for export",
        location=LocationItem(name="LOS ANGELES, CA"),
        facility="UP-ICTF",
        est_or_actual="A",
        task_id=1,
    )

    assert results[10] == ContainerStatusItem(
        container_key="CMAU4352196",
        local_date_time="Wed 05 Feb 2020 18:22",
        description="Loaded on board",
        location=LocationItem(name="LOS ANGELES, CA"),
        facility="FENIX MARINE TERMINAL",
        est_or_actual="A",
        task_id=1,
    )
