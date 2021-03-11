from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aplu import ContainerStatusRoutingRule, CarrierApluSpider
from test.spiders.carrier_aplu import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_basic', 'SHSE015942', 'SHSE015942'),
    ('02_no_pod_time_and_status', 'AYU0320031', 'AYU0320031'),
])
def test_container_status_routing_rule(sample_loader, sub, mbl_no, container_no):
    html_text = sample_loader.read_file(sub, 'container.html')

    option = ContainerStatusRoutingRule.build_request_option(
        mbl_no=mbl_no, container_no=container_no, base_url=CarrierApluSpider.base_url)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=option.url,
            meta={
                'container_no': container_no,
            },
        ),
    )

    routing_rule = ContainerStatusRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)