from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='SITC WEIHAI',
        vessel='SITC WEIHAI',
        voyage='1822S',
        pol=LocationItem(name='NINGBO'),
        pod=LocationItem(name='HAIPHONG'),
        etd=None,
        atd='2018-10-02 00:40',
        eta=None,
        ata='2018-10-06 08:48',
    )

    assert results[1] == VesselItem(
        vessel_key='SITC WEIHAI',
        vessel='SITC WEIHAI',
        voyage='1822S',
        pol=LocationItem(name='NINGBO'),
        pod=LocationItem(name='HAIPHONG'),
        etd=None,
        atd='2018-10-02 00:40',
        eta=None,
        ata='2018-10-06 08:48',
    )
