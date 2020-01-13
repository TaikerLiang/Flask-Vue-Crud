import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490855',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Laem Chabang, Thailand"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Cape Flint',
        vessel='Cape Flint',
        voyage='29',
        etd='27-Sep-2019',
        eta='06-Oct-2019',
    )

    assert results[2] == ContainerItem(
        container_key='ZCSU2764374',
        container_no='ZCSU2764374',
    )

    assert isinstance(results[3], scrapy.Request)
