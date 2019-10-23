from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='BUDAPEST EXPRESS',
        vessel='BUDAPEST EXPRESS',
        voyage='0056E',
        pol='YANTIAN, GUANGDONG,CHINA',
        pod='PUSAN,KOREA REPUBLIC OF',
        etd=None,
        atd='2019-10-03 20:35',
        eta=None,
        ata='2019-10-11 18:00',
    )

    assert results[1] == VesselItem(
        vessel_key='YM UPWARD',
        vessel='YM UPWARD',
        voyage='0062E',
        pol='PUSAN,KOREA REPUBLIC OF',
        pod='LOS ANGELES, CA,UNITED STATES',
        etd=None,
        atd='2019-10-13 19:50',
        eta='2019-10-24 14:00',
        ata=None,
    )
