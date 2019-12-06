from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_gosu import CarrierGosuSpider, ContainerStatusRoutingRule
from test.spiders.carrier_gosu import container_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,eta,container_no', [
    ('01_basic', 'GOSUNGB9490855', '06-Oct-2019', 'ZCSU2764374'),
])
def test_main_info_routing_rule(sub, mbl_no, eta, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'container_status.html')

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no=mbl_no, eta=eta, container_no=container_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'container_key': container_no,
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
            }
        )
    )

    spider = CarrierGosuSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)