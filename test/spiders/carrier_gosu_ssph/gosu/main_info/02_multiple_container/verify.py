from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUNGB9490903',
        por=LocationItem(name=None),
        pol=LocationItem(name="Ningbo , China. People's Republic"),
        pod=LocationItem(name="Laem Chabang, Thailand"),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == VesselItem(
        vessel_key='Cape Flint',
        vessel='Cape Flint',
        voyage='30',
        etd='19-Oct-2019',
        eta='27-Oct-2019',
        pol=LocationItem(name="Ningbo (ZJ), China. People's Republic (POL)"),
        pod=LocationItem(name='Laem Chabang, Thailand (POD)'),
    )

    assert results[2] == ContainerItem(
        container_key='ZCSU2589311',
        container_no='ZCSU2589311',
    )

    assert isinstance(results[3], RoutingRequest)

    assert results[4] == ContainerItem(
        container_key='ZCSU2577162',
        container_no='ZCSU2577162',
    )

    assert isinstance(results[5], RoutingRequest)

    assert results[6] == ContainerItem(
        container_key='ZCSU2574775',
        container_no='ZCSU2574775',
    )

    assert isinstance(results[7], RoutingRequest)

    assert results[8] == ContainerItem(
        container_key='ZCSU2615663',
        container_no='ZCSU2615663',
    )
