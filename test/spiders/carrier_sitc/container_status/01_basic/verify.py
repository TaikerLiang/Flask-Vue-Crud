from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='TEXU1590997',
        description='MT (EMPTY CONTAINER)',
        local_date_time='2018-12-08',
        location=LocationItem(name='BANGKOK'),
    )

    assert results[1] == ContainerStatusItem(
        container_key='TEXU1590997',
        description='ID (INBOUND DELIVERY)',
        local_date_time='2018-12-07',
        location=LocationItem(name='BANGKOK'),
    )

    assert results[2] == ContainerStatusItem(
        container_key='TEXU1590997',
        description='IC (INBOUND IN CY)',
        local_date_time='2018-12-05',
        location=LocationItem(name='BANGKOK'),
    )

    assert results[3] == ContainerStatusItem(
        container_key='TEXU1590997',
        description='VL (LOADED ONTO VESSEL)',
        local_date_time='2018-11-23',
        location=LocationItem(name='NINGBO'),
    )
