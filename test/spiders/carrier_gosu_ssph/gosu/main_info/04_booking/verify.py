from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert results[0] == MblItem(
        mbl_no=None,
        por=LocationItem(name=None),
        pol=LocationItem(name="Kaohsiung, Taiwan"),
        pod=LocationItem(name="Manila North Port, Philippines"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Scio Sky',
        vessel='Scio Sky',
        voyage='10',
        etd='27-Dec-2019',
        eta='31-Dec-2019',
        pol=LocationItem(name='Kaohsiung, Taiwan (POL)'),
        pod=LocationItem(name='Manila North Port, Philippines (POD)'),
    )

    assert results[2] == ContainerItem(
        container_key='TTNU5185836',
        container_no='TTNU5185836',
    )

    assert isinstance(results[3], RoutingRequest)
