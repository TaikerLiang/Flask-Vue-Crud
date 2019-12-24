from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='WHSU5204960',
        container_no='WHSU5204960',
    )
