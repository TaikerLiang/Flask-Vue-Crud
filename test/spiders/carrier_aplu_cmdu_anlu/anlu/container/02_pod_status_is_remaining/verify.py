from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='KAOHSIUNG (TW)'),
        pod=LocationItem(name='ADELAIDE (AU)'),
        final_dest=LocationItem(name=None),
        eta='Wed 11 Dec 2019 03:00',
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key='TEXU1028151',
        container_no='TEXU1028151',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TEXU1028151',
        local_date_time='Mon 11 Nov 2019 17:45',
        description='Empty to shipper',
        location=LocationItem(name='KAOHSIUNG'),
        est_or_actual='A',
    )

    assert results[7] == ContainerStatusItem(
        container_key='TEXU1028151',
        local_date_time='Wed 11 Dec 2019 03:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='ADELAIDE'),
        est_or_actual='E'
    )
