import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490903',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Laem Chabang, Thailand"),
        final_dest=LocationItem(name=None),
        etd='19-Oct-2019',
        eta='27-Oct-2019',
        vessel='Cape Flint',
        voyage='30',
    )

    assert results[1] == ContainerItem(
        container_key='ZCSU2589311',
        container_no='ZCSU2589311',
    )

    assert isinstance(results[2], scrapy.Request)

    assert results[3] == ContainerItem(
        container_key='ZCSU2577162',
        container_no='ZCSU2577162',
    )

    assert isinstance(results[4], scrapy.Request)

    assert results[5] == ContainerItem(
        container_key='ZCSU2574775',
        container_no='ZCSU2574775',
    )

    assert isinstance(results[6], scrapy.Request)

    assert results[7] == ContainerItem(
        container_key='ZCSU2615663',
        container_no='ZCSU2615663',
    )
