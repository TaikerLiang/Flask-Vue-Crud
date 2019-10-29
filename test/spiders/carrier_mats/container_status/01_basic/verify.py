from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='MATU2332036',
        description='RETURNED FROM CONSIGNEE',
        local_date_time='16/10/2019 14:11:00',
        location=LocationItem(name='LONG BEACH (CA)'),
    )