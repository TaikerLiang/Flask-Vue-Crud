from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        pol=LocationItem(un_lo_code='CNTAO'),
        vessel='COSCO ITALY',
        voyage='033E',
        etd='2019/11/12',
    )

    assert results[1] == VesselItem(
        pod=LocationItem(un_lo_code='USLAX'),
        vessel='COSCO ITALY',
        voyage='033E',
        eta='2019/10/24',
    )
