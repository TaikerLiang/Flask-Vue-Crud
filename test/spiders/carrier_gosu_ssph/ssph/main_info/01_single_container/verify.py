import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHJOR8017471',
        por=LocationItem(name=None),
        pol=LocationItem(name="Tanjung Pelepas, Malaysia"),
        pod=LocationItem(name="Savannah , U.S.A."),
        final_dest=LocationItem(name='Atlanta , U.S.A.'),
        etd='23-Nov-2019',
        eta='26-Dec-2019',
        vessel='Maersk Semakau',
        voyage='8',
    )

    assert results[1] == ContainerItem(
        container_key='ZCSU8832075',
        container_no='ZCSU8832075',
    )

    assert isinstance(results[2], scrapy.Request)
