from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='TEXU1585331',
        container_no='TEXU1585331',
    )
