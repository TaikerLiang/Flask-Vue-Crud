import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490840',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Ho Chi Minh City, Vietnam"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Cimbria',
        vessel='Cimbria',
        voyage='228',
        etd='27-Sep-2019',
        eta=None,
    )

    assert results[2] == ContainerItem(
        container_key='ZCSU8696662',
        container_no='ZCSU8696662',
    )

    assert isinstance(results[3], scrapy.Request)

    assert results[4] == ContainerItem(
        container_key='CAIU9220899',
        container_no='CAIU9220899',
    )

    assert isinstance(results[5], scrapy.Request)

    assert results[6] == ContainerItem(
        container_key='ZCSU8706565',
        container_no='ZCSU8706565',
    )

    assert isinstance(results[7], scrapy.Request)

    assert results[8] == ContainerItem(
        container_key='ZCSU8409757',
        container_no='ZCSU8409757',
    )

    assert isinstance(results[9], scrapy.Request)
