from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='SHANGHAI (CN)'),
        pod=LocationItem(name='MIAMI, FL (US)'),
        final_dest=LocationItem(name=None),
        eta='Fri 27 Sep 2019 07:00',
    )

    assert results[1] == ContainerItem(
        container_key='UESU5087866',
        container_no='UESU5087866',
    )

    assert results[2] == ContainerStatusItem(
        container_key='UESU5087866',
        local_date_time='Wed 14 Aug 2019 23:07',
        description='Empty to shipper',
        location=LocationItem(name='SHANGHAI'),
        est_or_actual='A',
    )

    assert results[5] == ContainerStatusItem(
        container_key='UESU5087866',
        local_date_time='Fri 27 Sep 2019 07:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='MIAMI'),
        est_or_actual='E',
    )
