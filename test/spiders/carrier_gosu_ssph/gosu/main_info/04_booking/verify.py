import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no=None,
        por=LocationItem(name=None),
        pol=LocationItem(name="Kaohsiung, Taiwan"),
        pod=LocationItem(name="Manila North Port, Philippines"),
        final_dest=LocationItem(name=None),
        etd='27-Dec-2019',
        eta='31-Dec-2019',
        vessel='Scio Sky',
        voyage='10',
    )

    assert results[1] == ContainerItem(
        container_key='TTNU5185836',
        container_no='TTNU5185836',
    )

    assert isinstance(results[2], scrapy.Request)
