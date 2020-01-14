from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert results[0] == ContainerItem(
        container_key='DFSU7597714',
        container_no='DFSU7597714',
    )

    assert isinstance(results[1], RoutingRequest)

    assert isinstance(results[2], RoutingRequest)

    assert results[3] == ContainerItem(
        container_key='WHSU5323281',
        container_no='WHSU5323281',
    )

    assert isinstance(results[4], RoutingRequest)

    assert isinstance(results[5], RoutingRequest)
