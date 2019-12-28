from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(
            vessel_key='MSC BARBARA',
            vessel='MSC BARBARA',
            voyage='939',
            pol='Shanghai CNSHA',
            pod=None,
            etd='Thu 26-Sep-2019',
            eta=None,
        )
