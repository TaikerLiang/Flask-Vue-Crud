import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490840',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Ho Chi Minh City, Vietnam"),
        final_dest=LocationItem(name=None),
        etd='27-Sep-2019',
        eta=None,
        vessel='Cimbria',
        voyage='228',
    )

    assert results[1] == ContainerItem(
        container_key='ZCSU8696662',
        container_no='ZCSU8696662',
    )

    assert isinstance(results[2], scrapy.Request)

    assert results[3] == ContainerItem(
        container_key='CAIU9220899',
        container_no='CAIU9220899',
    )

    assert isinstance(results[4], scrapy.Request)

    assert results[5] == ContainerItem(
        container_key='ZCSU8706565',
        container_no='ZCSU8706565',
    )

    assert isinstance(results[6], scrapy.Request)

    assert results[7] == ContainerItem(
        container_key='ZCSU8409757',
        container_no='ZCSU8409757',
    )

    assert isinstance(results[8], scrapy.Request)
