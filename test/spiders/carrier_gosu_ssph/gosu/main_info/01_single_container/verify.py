import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490855',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Laem Chabang, Thailand"),
        final_dest=LocationItem(name=None),
        etd='27-Sep-2019',
        eta='06-Oct-2019',
        vessel='Cape Flint',
        voyage='29',
    )

    assert results[1] == ContainerItem(
        container_key='ZCSU2764374',
        container_no='ZCSU2764374',
    )

    assert isinstance(results[2], scrapy.Request)
