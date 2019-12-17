from crawler.spiders.carrier_aplu_cmdu_anlc import ContainerStatusRoutingRule, CarrierAnlcSpider
from test.spiders.utils import extract_url_from


def verify(results):
    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='AWT0143454', container_no='TEXU1028151', base_url=CarrierAnlcSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[0].url == url

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='AWT0143454', container_no='AMCU2500184', base_url=CarrierAnlcSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[1].url == url

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='AWT0143454', container_no='TLLU1233702', base_url=CarrierAnlcSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[2].url == url

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no='AWT0143454', container_no='TCLU7717882', base_url=CarrierAnlcSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    assert results[3].url == url
