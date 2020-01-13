import scrapy

from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHLAX0137883',
        por=LocationItem(name='Cincinnati , U.S.A.'),
        pol=LocationItem(name='Savannah , U.S.A.'),
        pod=LocationItem(name="Port Klang, Malaysia"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Axel Maersk',
        vessel='Axel Maersk',
        voyage='3',
        etd='04-Aug-2019',
        eta='18-Sep-2019',
    )

    assert results[2] == VesselItem(
        vessel_key='Nanta Bhum',
        vessel='Nanta Bhum',
        voyage='3',
        etd='25-Sep-2019',
        eta='26-Sep-2019',
    )

    assert results[3] == ContainerItem(
        container_key='CRSU9052059',
        container_no='CRSU9052059',
    )

    assert isinstance(results[4], scrapy.Request)

    assert results[5] == ContainerItem(
        container_key='ZCSU6507651',
        container_no='ZCSU6507651',
    )

    assert isinstance(results[6], scrapy.Request)

    assert results[7] == ContainerItem(
        container_key='TGBU7177776',
        container_no='TGBU7177776',
    )

    assert isinstance(results[8], scrapy.Request)

    assert results[9] == ContainerItem(
        container_key='TLLU4309870',
        container_no='TLLU4309870',
    )

    assert isinstance(results[10], scrapy.Request)

    assert results[11] == ContainerItem(
        container_key='TLLU4586128',
        container_no='TLLU4586128',
    )

    assert isinstance(results[12], scrapy.Request)

    assert results[13] == ContainerItem(
        container_key='ZCSU8528036',
        container_no='ZCSU8528036',
    )

    assert isinstance(results[14], scrapy.Request)

    assert results[15] == ContainerItem(
        container_key='ZCSU8528268',
        container_no='ZCSU8528268',
    )
