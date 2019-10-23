from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='YM UNICORN',
        vessel='YM UNICORN',
        voyage='0040E',
        pol='SHANGHAI, SHANGHAI,CHINA',
        pod='LOS ANGELES, CA,UNITED STATES',
        etd=None,
        atd='2019-10-06 04:00',
        eta='2019-10-18 14:00',
        ata=None,
    )
