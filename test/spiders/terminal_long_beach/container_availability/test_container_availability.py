from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager
from crawler.core_terminal.tms_share_spider import SeleniumRoutingRule
from crawler.spiders.terminal_long_beach import TerminalPctSpider
from test.spiders.terminal_long_beach import container_availability


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_availability, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_basic', 'TGHU0113128'),
    ],
)
def test_selenium_routing_rule(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SeleniumRoutingRule.build_request_option(
        container_nos=[container_no],
        terminal_id=TerminalPctSpider.terminal_id,
        company_info=TerminalPctSpider.company_info,
    )

    response = TextResponse(
        url=request_option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={
                RuleManager.META_TERMINAL_CORE_RULE_NAME: SeleniumRoutingRule.name,
                'container_nos': [container_no],
                'terminal_id': TerminalPctSpider.terminal_id,
                'company_info': TerminalPctSpider.company_info,
            },
        ),
    )

    routing_rule = SeleniumRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,invalid_no_item',
    [
        ('e01_invalid_container_no', 'FCIU2218769', InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SeleniumRoutingRule.build_request_option(
        container_nos=[container_no],
        terminal_id=TerminalPctSpider.terminal_id,
        company_info=TerminalPctSpider.company_info,
    )

    response = TextResponse(
        url=request_option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    routing_rule = SeleniumRoutingRule()
    assert list(routing_rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
