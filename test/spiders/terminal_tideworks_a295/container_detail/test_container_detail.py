from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.tideworks_share_spider import ContainerDetailRoutingRule
from test.spiders.terminal_tideworks_a295 import container_detail
from crawler.spiders.terminal_tideworks_a295 import TerminalTideworksConleySpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_detail, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,',
    [
        ("01_basic", "MEDU7322906"),
        ("02_punct_in_vessel_name", "MSDU7655308"),
    ],
)
def test_container_detail_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    container_url = f'/fc-MCT/import/default.do?method=container&eqptNbr={container_no}&gkey=20913717'
    request_option = ContainerDetailRoutingRule.build_request_option(
        container_url=container_url,
        company_info=TerminalTideworksConleySpider.company_info
    )

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
        ),
    )

    rule = ContainerDetailRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
