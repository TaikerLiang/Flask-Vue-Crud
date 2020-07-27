from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_cosu import BookingMainInfoRoutingRule


def verify(results, mbl_no):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == BookingMainInfoRoutingRule.name

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == BookingMainInfoRoutingRule.name
