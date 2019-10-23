from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='AS MORGANA',
        vessel='AS MORGANA',
        voyage='1905E',
        pol='SHANGHAI,CHINA',
        pod='VANCOUVER,BC,CANADA',
        etd=None,
        atd='2019-09-04 02:30',
        eta=None,
        ata='2019-09-17 17:36',
    )
