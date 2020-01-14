from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHLAX0137876',
        por=LocationItem(name='Cincinnati , U.S.A.'),
        pol=LocationItem(name='Savannah , U.S.A.'),
        pod=LocationItem(name="Port Klang, Malaysia"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Axel Maersk',
        vessel='Axel Maersk',
        voyage='3',
        etd='04-Aug-2019',
        eta='18-Sep-2019',
        pol=LocationItem(name='Savannah (GA), U.S.A. (POL)'),
        pod=LocationItem(name='Singapore, Singapore (Transshipment)'),
    )

    assert results[2] == VesselItem(
        vessel_key='Nanta Bhum',
        vessel='Nanta Bhum',
        voyage='3',
        etd='25-Sep-2019',
        eta='26-Sep-2019',
        pol=LocationItem(name='Singapore, Singapore (Transshipment)'),
        pod=LocationItem(name='Port Klang, Malaysia (POD)'),
    )

    assert results[3] == ContainerItem(
        container_key='ZCSU7133387',
        container_no='ZCSU7133387',
    )

    assert isinstance(results[4], RoutingRequest)

    assert results[5] == ContainerItem(
        container_key='ZCSU8756838',
        container_no='ZCSU8756838',
    )

    assert isinstance(results[6], RoutingRequest)

    assert results[7] == ContainerItem(
        container_key='ZCSU8564120',
        container_no='ZCSU8564120',
    )

    assert isinstance(results[8], RoutingRequest)

    assert results[9] == ContainerItem(
        container_key='FSCU8165710',
        container_no='FSCU8165710',
    )
