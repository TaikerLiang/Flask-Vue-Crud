from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_ymlu import ContainerStatusRoutingRule
from test.spiders.carrier_ymlu import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no,follow_url', [
    (
        '01',
        'W209131160',
        'YMLU3555177',
        'ctconnect.aspx?rdolType=BL&ctnrno=YMLU3555177&blno=W209131160&movertype=31&lifecycle=2',
    ),
    (
        '02_eol_in_location',
        'W232317137',
        'DRYU4228115',
        'ctconnect.aspx?rdolType=BL&ctnrno=DRYU4228115&blno=W232317137&movertype=11&lifecycle=1',
    ),
])
def test_main_info_routing_rule(sub, mbl_no, container_no, follow_url, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    container_status_request_option = ContainerStatusRoutingRule.build_request_option(
        follow_url=follow_url, container_no=container_no, headers={}
    )

    response = TextResponse(
        url=container_status_request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=container_status_request_option.url,
            meta=container_status_request_option.meta,
        )
    )

    rule = ContainerStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
