from crawler.spiders.carrier_aplu_cmdu_anlc import ContainerStatusRoutingRule, CarrierCmduSpider
from test.spiders.utils import extract_url_from


def verify(results):
    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='NBSF301194', container_no='ECMU9893257', base_url=CarrierCmduSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[0].url == url

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='NBSF301194', container_no='ECMU9836072', base_url=CarrierCmduSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[1].url == url
