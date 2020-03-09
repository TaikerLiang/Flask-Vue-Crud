from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='NANJING (CN)'),
        pod=LocationItem(name='LOS ANGELES, CA (US)'),
        final_dest=LocationItem(name=None),
        eta=None,
    )

    assert results[1] == ContainerItem(
        container_key='CNCU1610540',
        container_no='CNCU1610540',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CNCU1610540',
        local_date_time='Wed 18 Sep 2019 23:53',
        description='Empty to shipper',
        location=LocationItem(name='NANJING'),
        est_or_actual='A',
    )

    assert results[7] == ContainerStatusItem(
        container_key='CNCU1610540',
        local_date_time='Wed 16 Oct 2019 05:30',
        description='Arrival final port of discharge',
        location=LocationItem(name='LOS ANGELES, CA'),
        est_or_actual='E'
    )
