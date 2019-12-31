from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_hdmu import ContainerRoutingRule
from test.spiders.carrier_hdmu import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no,container_index', [
    ('01_first', 'QSWB8011462', 'DFSU6717570', 2),
])
def test_container_routing_rule(sub, mbl_no, sample_loader, container_no, container_index):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_config = ContainerRoutingRule.build_request_config(mbl_no=mbl_no, container_index=container_index, h_num=0)

    response = TextResponse(
        url=request_config.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_config.url,
            meta={
                'mbl_no': mbl_no,
                'container_index': container_index,
            }
        )
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
