from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='ZCSU8832075',
        description='Empty container dispatched from inland point to Customer',
        location=LocationItem(name='Tanjung Pelepas, Malaysia'),
        local_date_time='18-Nov-2019',
    )

    assert results[3] == ContainerStatusItem(
        container_key='ZCSU8832075',
        description='Carrier Release',
        location=LocationItem(name="Savannah , U.s.a."),
        local_date_time='18-Dec-2019',
    )

    assert results[5] == ContainerStatusItem(
        container_key='ZCSU8832075',
        description='Customs release',
        location=LocationItem(name="Savannah , U.s.a."),
        local_date_time='27-Dec-2019',
    )
