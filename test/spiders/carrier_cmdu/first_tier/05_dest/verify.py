from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='NINGBO (CN)'),
        pod=LocationItem(name='SAVANNAH, GA (US)'),
        final_dest=LocationItem(name='ATLANTA, GA (US)'),
        eta='Thu 05 Sep 2019 06:00',
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key='CMAU4349470',
        container_no='CMAU4349470',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CMAU4349470',
        local_date_time='Thu 18 Jul 2019 22:00',
        description='Empty to shipper',
        location=LocationItem(name='NINGBO'),
        est_or_actual='A',
    )

    assert results[7] == ContainerStatusItem(
        container_key='CMAU4349470',
        local_date_time='Thu 05 Sep 2019 06:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='SAVANNAH'),
        est_or_actual='E',
    )

def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='NINGBO (CN)'),
        pod=LocationItem(name='SAVANNAH, GA (US)'),
        final_dest=LocationItem(name='ATLANTA, GA (US)'),
        eta='Thu 05 Sep 2019 06:00',
        ata=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='CMAU4349470',
        container_no='CMAU4349470',
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key='CMAU4349470',
        local_date_time='Thu 18 Jul 2019 22:00',
        description='Empty to shipper',
        location=LocationItem(name='NINGBO'),
        est_or_actual='A',
        task_id=1,
    )

    assert results[7] == ContainerStatusItem(
        container_key='CMAU4349470',
        local_date_time='Thu 05 Sep 2019 06:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='SAVANNAH'),
        est_or_actual='E',
        task_id=1,
    )