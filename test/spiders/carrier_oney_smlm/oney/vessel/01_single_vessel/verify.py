from crawler.core_carrier.items_new import LocationItem, VesselItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key="YM UNICORN",
        vessel="YM UNICORN",
        voyage="0040E",
        pol=LocationItem(name="SHANGHAI, SHANGHAI,CHINA"),
        pod=LocationItem(name="LOS ANGELES, CA,UNITED STATES"),
        etd=None,
        atd="2019-10-06 04:00",
        eta="2019-10-18 14:00",
        ata=None,
    )
