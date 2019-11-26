from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='DFSU7597714',
        container_no='DFSU7597714',
    )
