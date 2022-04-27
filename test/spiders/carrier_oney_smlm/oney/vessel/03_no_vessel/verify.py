from crawler.core_carrier.items_new import VesselItem


def verify(results):
    assert results[0] == VesselItem()
