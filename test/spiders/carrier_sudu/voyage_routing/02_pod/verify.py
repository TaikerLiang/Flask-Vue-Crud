from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(
            vessel_key='MSC BARBARA',
            vessel='MSC BARBARA',
            voyage='939',
            pol=None,
            pod='Houston USHOU',
            etd=None,
            eta='Thu 24-Oct-2019',
        )
