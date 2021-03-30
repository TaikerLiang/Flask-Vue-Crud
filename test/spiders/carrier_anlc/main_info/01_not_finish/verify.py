from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='KAOHSIUNG (TW)'),
        pod=LocationItem(name='WELLINGTON (NZ)'),
        final_dest=LocationItem(name=None),
        eta='Thu 21 Nov 2019 14:30',
    )

    assert results[1] == ContainerItem(
        container_key='TCLU7705557',
        container_no='TCLU7705557',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TCLU7705557',
        local_date_time='Fri 18 Oct 2019 09:14',
        description='Empty to shipper',
        location=LocationItem(name='KAOHSIUNG'),
        est_or_actual='A',
    )

    assert results[7] == ContainerStatusItem(
        container_key='TCLU7705557',
        local_date_time='Thu 21 Nov 2019 14:30',
        description='Arrival final port of discharge',
        location=LocationItem(name='WELLINGTON'),
        est_or_actual='E',
    )
