from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='BUDAPEST EXPRESS',
        vessel='BUDAPEST EXPRESS',
        voyage='0056E',
        pol=LocationItem(name='YANTIAN, GUANGDONG,CHINA'),
        pod=LocationItem(name='PUSAN,KOREA REPUBLIC OF'),
        etd=None,
        atd='2019-10-03 20:35',
        eta=None,
        ata='2019-10-11 18:00',
        task_id=1,
    )

    assert results[1] == VesselItem(
        vessel_key='YM UPWARD',
        vessel='YM UPWARD',
        voyage='0062E',
        pol=LocationItem(name='PUSAN,KOREA REPUBLIC OF'),
        pod=LocationItem(name='LOS ANGELES, CA,UNITED STATES'),
        etd=None,
        atd='2019-10-13 19:50',
        eta='2019-10-24 14:00',
        ata=None,
        task_id=1,
    )
