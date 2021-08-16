from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name='KANSAS CITY, KS (US)'),
        pol=LocationItem(name='LOS ANGELES, CA (US)'),
        pod=LocationItem(name='TAIPEI (TW)'),
        final_dest=LocationItem(name='KEELUNG (TW)'),
        eta=None,
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key='TCNU3341069',
        container_no='TCNU3341069',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TCNU3341069',
        local_date_time='Sun 13 Oct 2019 20:51',
        description='Empty to shipper',
        location=LocationItem(name='KANSAS CITY, KS'),
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='TCNU3341069',
        local_date_time='Sun 20 Oct 2019 12:06',
        description='Container on rail for export',
        location=LocationItem(name='BARSTOW, CA'),
        est_or_actual='A',
    )

def multi_verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name='KANSAS CITY, KS (US)'),
        pol=LocationItem(name='LOS ANGELES, CA (US)'),
        pod=LocationItem(name='TAIPEI (TW)'),
        final_dest=LocationItem(name='KEELUNG (TW)'),
        eta=None,
        ata=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='TCNU3341069',
        container_no='TCNU3341069',
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key='TCNU3341069',
        local_date_time='Sun 13 Oct 2019 20:51',
        description='Empty to shipper',
        location=LocationItem(name='KANSAS CITY, KS'),
        est_or_actual='A',
        task_id=1,
    )

    assert results[6] == ContainerStatusItem(
        container_key='TCNU3341069',
        local_date_time='Sun 20 Oct 2019 12:06',
        description='Container on rail for export',
        location=LocationItem(name='BARSTOW, CA'),
        est_or_actual='A',
        task_id=1,
    )