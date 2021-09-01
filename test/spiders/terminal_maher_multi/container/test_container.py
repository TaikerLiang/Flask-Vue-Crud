from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager
from crawler.spiders.terminal_maher_multi import TerminalMaherMultiSpider, SearchRoutingRule
from test.spiders.terminal_maher import container

@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_basic', 'EISU9407701'),
        ('02_available', 'CSNU7920778'),
    ],
)
def test_search_routing_rule(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SearchRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={
                RuleManager.META_TERMINAL_CORE_RULE_NAME: SearchRoutingRule.name,
                'container_no_list': [container_no],
            },
        ),
    )

    routing_rule = SearchRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

@pytest.mark.parametrize(
    'sub,container_no,invalid_no_item',
    [
        ('e01_invalid_container_no', 'EISU9487741', InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SearchRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    routing_rule = SearchRoutingRule()
    assert list(routing_rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
