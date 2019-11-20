from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name='TAICHUNG (TW)'),
        pol=LocationItem(name='TAIPEI (TW)'),
        pod=LocationItem(name='LOS ANGELES, CA (US)'),
        final_dest=LocationItem(name='DALLAS, TX (US)'),
        eta=None,
        ata='Wed 17 Jul 2019 15:11',
    )

    assert results[1] == ContainerItem(
        container_key='CAIU9073761',
        container_no='CAIU9073761',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CAIU9073761',
        local_date_time='Mon 24 Jun 2019 08:40',
        description='Empty to shipper',
        location=LocationItem(name='TAICHUNG'),
        est_or_actual='A',
    )

    assert results[17] == ContainerStatusItem(
        container_key='CAIU9073761',
        local_date_time='Wed 31 Jul 2019 18:23',
        description='Empty in depot',
        location=LocationItem(name='DALLAS, TX'),
        est_or_actual='A'
    )
