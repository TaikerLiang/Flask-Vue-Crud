from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='TEXU1590148',
        description='outbound pickup',
        local_date_time='2021-07-05',
        location=LocationItem(name='shanghai'),
    )

    assert results[1] == ContainerStatusItem(
        container_key='TEXU1590148',
        description='loaded onto vessel',
        local_date_time='2021-07-19',
        location=LocationItem(name='shanghai'),
    )

    assert results[2] == ContainerStatusItem(
        container_key='TEXU1590148',
        description='inbound in cy',
        local_date_time='2021-07-24',
        location=LocationItem(name='ho chi minh'),
    )

    assert results[3] == ContainerStatusItem(
        container_key='TEXU1590148',
        description='inbound delivery',
        local_date_time='2021-07-27',
        location=LocationItem(name='ho chi minh'),
    )

    assert results[4] == ContainerStatusItem(
        container_key='TEXU1590148',
        description='empty container',
        local_date_time='2021-07-27',
        location=LocationItem(name='ho chi minh'),
    )
