from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert isinstance(results[0], RoutingRequest)
