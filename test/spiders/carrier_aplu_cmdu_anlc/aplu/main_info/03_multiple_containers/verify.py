from crawler.spiders.carrier_aplu_cmdu_anlc import CarrierApluSpider, ContainerStatusRoutingRule
from test.spiders.utils import extract_url_from


def verify(results):
    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='SHSE015942', container_no='TCNU1868370', base_url=CarrierApluSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[0].url == url

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='SHSE015942', container_no='APHU6968583', base_url=CarrierApluSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[1].url == url
