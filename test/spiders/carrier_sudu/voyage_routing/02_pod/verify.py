from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
            vessel_key='Houston USHOU Arrival',
            vessel='MSC BARBARA',
            voyage='939',
            pol=LocationItem(name=None),
            pod=LocationItem(name='Houston USHOU'),
            etd=None,
            eta='Thu 24-Oct-2019',
        )
