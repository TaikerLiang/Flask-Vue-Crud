from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_aclu import DetailTrackingRoutingRule


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == DetailTrackingRoutingRule.name
