from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.tideworks_share_spider import ContainerDetailRoutingRule
from crawler.spiders.terminal_pier_multi import TerminalPierSpider
from test.spiders.terminal_pier_multi import container_detail


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_detail, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,',
    [
        ('01_basic', 'WHSU6189984'),
    ],
)
def test_container_detail_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    container_url = f'/fc-PA/import/default.do?method=container&eqptNbr={container_no}&gkey=17092328'
    request_option = ContainerDetailRoutingRule.build_request_option(
        container_url=container_url,
        company_info=TerminalPierSpider.company_info,
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