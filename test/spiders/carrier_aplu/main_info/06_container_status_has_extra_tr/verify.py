from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name='KANSAS CITY, KS (US)'),
        pol=LocationItem(name='LOS ANGELES, CA (US)'),
        pod=LocationItem(name='TAIPEI (TW)'),
        final_dest=LocationItem(name='KEELUNG (TW)'),
        eta=None,
    )

    assert results[1] == ContainerItem(
        container_key='CMAU4352196',
        container_no='CMAU4352196',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CMAU4352196',
        local_date_time='Fri 17 Jan 2020 13:54',
        description='Empty to shipper',
        location=LocationItem(name='SALT LAKE CITY, UT'),
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='CMAU4352196',
        local_date_time='Sat 25 Jan 2020 09:00',
        description='Container on rail for export',
        location=LocationItem(name='LOS ANGELES, CA'),
        est_or_actual='A',
    )

    assert results[10] == ContainerStatusItem(
        container_key='CMAU4352196',
        local_date_time='Wed 05 Feb 2020 18:22',
        description='Loaded on board',
        location=LocationItem(name='LOS ANGELES, CA'),
        est_or_actual='A',
    )
