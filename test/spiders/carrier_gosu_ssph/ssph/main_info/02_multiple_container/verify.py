import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHLAX0137876',
        por=LocationItem(name='Cincinnati , U.S.A.'),
        pol=LocationItem(name='Savannah , U.S.A.'),
        pod=LocationItem(name="Port Klang, Malaysia"),
        final_dest=LocationItem(name=None),
        etd=None,
        eta=None,
        vessel=None,
        voyage=None,
    )

    assert results[1] == ContainerItem(
        container_key='ZCSU7133387',
        container_no='ZCSU7133387',
    )

    assert isinstance(results[2], scrapy.Request)

    assert results[3] == ContainerItem(
        container_key='ZCSU8756838',
        container_no='ZCSU8756838',
    )

    assert isinstance(results[4], scrapy.Request)

    assert results[5] == ContainerItem(
        container_key='ZCSU8564120',
        container_no='ZCSU8564120',
    )

    assert isinstance(results[6], scrapy.Request)

    assert results[7] == ContainerItem(
        container_key='FSCU8165710',
        container_no='FSCU8165710',
    )
