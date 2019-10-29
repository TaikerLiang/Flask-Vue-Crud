import scrapy

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem, ContainerStatusItem


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name='NINGBO'),
        pol=LocationItem(name='NINGBO'),
        pod=LocationItem(name='LONG BEACH'),
        final_dest=LocationItem(name='LONG BEACH'),
    )

    assert results[1] == ContainerItem(
        container_key='MATU2310910',
        container_no='MATU2310910',
    )

    assert isinstance(results[2], scrapy.FormRequest)
