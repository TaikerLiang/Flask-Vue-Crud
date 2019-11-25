from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='BOMAR HAMBURG',
        vessel='BOMAR HAMBURG',
        voyage='1939E',
        pol=LocationItem(name='QINGDAO,CHINA,CHINA'),
        pod=LocationItem(name='BUSAN,REPUBLIC OF KOREA'),
        etd=None,
        atd='2019-10-01 12:45',
        eta=None,
        ata='2019-10-03 16:55',
    )

    assert results[1] == VesselItem(
        vessel_key='SM SHANGHAI',
        vessel='SM SHANGHAI',
        voyage='1907E',
        pol=LocationItem(name='BUSAN,REPUBLIC OF KOREA'),
        pod=LocationItem(name='LONG BEACH,CA,UNITED STATES'),
        etd=None,
        atd='2019-10-06 21:47',
        eta='2019-10-18 14:30',
        ata=None,
    )