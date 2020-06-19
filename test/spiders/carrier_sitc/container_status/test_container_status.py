from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_sitc import ContainerStatusRoutingRule
from test.spiders.carrier_sitc import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_basic', 'SITDNBBK351734', 'TEXU1590997'),
])
def test_container_status_routing_rule(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
                'mbl_no': mbl_no,
                'container_no': container_no,
                'container_key': container_no,
            }
        )
    )

    routing_rule = ContainerStatusRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
