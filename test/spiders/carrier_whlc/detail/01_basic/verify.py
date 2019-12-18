from crawler.core_carrier.items import VesselItem, LocationItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key='COSCO ITALY / 033E',
        vessel='COSCO ITALY',
        voyage='033E',
        pol=LocationItem(un_lo_code='CNTAO'),
        etd='2019/11/12',
    )

    assert results[1] == VesselItem(
        vessel_key='COSCO ITALY / 033E',
        vessel='COSCO ITALY',
        voyage='033E',
        pod=LocationItem(un_lo_code='USLAX'),
        eta='2019/10/24',
    )
