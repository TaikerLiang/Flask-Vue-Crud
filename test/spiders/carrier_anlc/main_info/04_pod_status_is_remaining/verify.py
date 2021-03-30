from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='KAOHSIUNG (TW)'),
        pod=LocationItem(name='FREMANTLE (AU)'),
        final_dest=LocationItem(name=None),
        eta='Fri 06 Dec 2019 06:00',
    )

    assert results[1] == ContainerItem(
        container_key='TLLU1230909',
        container_no='TLLU1230909',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TLLU1230909',
        local_date_time='Mon 11 Nov 2019 13:09',
        description='Empty to shipper',
        location=LocationItem(name='KAOHSIUNG'),
        est_or_actual='A',
    )

    assert results[7] == ContainerStatusItem(
        container_key='TLLU1230909',
        local_date_time='Fri 06 Dec 2019 06:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='FREMANTLE'),
        est_or_actual='E',
    )
