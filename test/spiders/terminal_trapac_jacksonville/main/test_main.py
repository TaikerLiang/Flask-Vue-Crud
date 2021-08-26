from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.trapac_share_spider import MainRoutingRule
from crawler.spiders.terminal_trapac_jacksonville import TerminalTrapacJackSpider
from test.spiders.terminal_trapac_jacksonville import main


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_basic', 'KKFU7819122'),
        ('02_no_holds', 'DRYU4301406'),
    ],
)
def test_main_routing_rule(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTrapacJackSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = MainRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

@pytest.mark.parametrize(
    'sub,container_no,invalid_no_item',
    [
        ('e01_invalid_container_no', 'KOCU442706', InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTrapacJackSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainRoutingRule()
    assert list(rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
