import scrapy

from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='WHSU5121845',
        container_no='WHSU5121845',
    )

    assert isinstance(results[1], scrapy.Request)

    assert len(results) == 2
