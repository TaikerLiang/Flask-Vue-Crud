from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem()

