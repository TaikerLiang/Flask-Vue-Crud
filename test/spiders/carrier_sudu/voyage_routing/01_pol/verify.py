from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='Shanghai CNSHA Departure',
        vessel='MSC BARBARA',
        voyage='939',
        pol=LocationItem(name='Shanghai CNSHA'),
        pod=LocationItem(name=None),
        etd='Thu 26-Sep-2019',
        eta=None,
    )
