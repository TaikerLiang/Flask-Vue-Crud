from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_ymlu import CarrierYmluSpider, MainInfoRoutingRule, ContainerStatusRoutingRule
from test.spiders.carrier_ymlu import container_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no,follow_url', [
    ('01', 'W209131160', 'YMLU3555177', 'ctconnect.aspx?rdolType=BL&ctnrno=YMLU3555177&'
                                        'blno=W209131160&movertype=31&lifecycle=2'),
])
def test_main_info_routing_rule(sub, mbl_no, container_no, follow_url, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    main_info_routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=mbl_no)
    main_info_url = extract_url_from(routing_request=main_info_routing_request)

    main_info_response = TextResponse(url=main_info_url)

    container_status_routing_request = ContainerStatusRoutingRule.build_routing_request(
        response=main_info_response, follow_url=follow_url, container_no=container_no)
    container_status_url = extract_url_from(routing_request=container_status_routing_request)

    response = TextResponse(
        url=container_status_url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=container_status_url,
            meta={
                'container_no': container_no,
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
            }
        )
    )

    spider = CarrierYmluSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
