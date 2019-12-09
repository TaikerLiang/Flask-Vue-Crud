from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='SITC HEBEI',
        vessel='SITC HEBEI',
        voyage='1820S',
        pol=LocationItem(name='NINGBO'),
        pod=LocationItem(name='BANGKOK'),
        etd=None,
        atd='2018-11-23 21:48',
        eta=None,
        ata='2018-12-04 05:30',
    )
