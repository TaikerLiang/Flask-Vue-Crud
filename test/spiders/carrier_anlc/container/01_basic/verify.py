from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='KAOHSIUNG (TW)'),
        pod=LocationItem(name='MELBOURNE (AU)'),
        final_dest=LocationItem(name=None),
        eta=None,
        ata='Wed 13 Nov 2019 09:08',
    )

    assert results[1] == ContainerItem(
        container_key='BHCU2231403',
        container_no='BHCU2231403',
    )

    assert results[2] == ContainerStatusItem(
        container_key='BHCU2231403',
        local_date_time='Thu 24 Oct 2019 16:41',
        description='Empty to shipper',
        location=LocationItem(name='KAOHSIUNG'),
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='BHCU2231403',
        local_date_time='Fri 15 Nov 2019 14:25',
        description='Container to consignee',
        location=LocationItem(name='MELBOURNE'),
        est_or_actual='A',
    )
