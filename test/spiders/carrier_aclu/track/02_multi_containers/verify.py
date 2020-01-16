from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert isinstance(results[0], RoutingRequest)
    assert isinstance(results[1], RoutingRequest)
    assert isinstance(results[2], RoutingRequest)
    assert isinstance(results[3], RoutingRequest)
    assert isinstance(results[4], RoutingRequest)
    assert isinstance(results[5], RoutingRequest)
    assert isinstance(results[6], RoutingRequest)
    assert isinstance(results[7], RoutingRequest)
    assert isinstance(results[8], RoutingRequest)
    assert isinstance(results[9], RoutingRequest)
