from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='TEXU1590997',
        container_no='TEXU1590997',
    )

    assert results[2] == ContainerItem(
        container_key='SEGU7343124',
        container_no='SEGU7343124',
    )
