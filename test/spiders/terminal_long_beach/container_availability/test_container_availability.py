from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.core_terminal.rules import RuleManager
from crawler.core_terminal.tms_share_spider import SeleniumRoutingRule
from test.spiders.terminal_long_beach import container_availability


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_availability, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_basic', 'NYKU5151837'),
    ],
)
def test_container_status_routing_rule(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SeleniumRoutingRule.build_request_option(token='', container_no=container_no)

    response = TextResponse(
        url=request_option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={
                RuleManager.META_TERMINAL_CORE_RULE_NAME: SeleniumRoutingRule.name,
                'container_no': container_no,
            },
        ),
    )

    routing_rule = SeleniumRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,expected_exception',
    [
        ('e01_invalid_container_no', 'FCIU2218769', TerminalInvalidContainerNoError),
    ],
)
def test_container_availability_handler_error(sub, container_no, expected_exception, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    request_option = SeleniumRoutingRule.build_request_option(token='', container_no=container_no)

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
    with pytest.raises(expected_exception=expected_exception):
        list(routing_rule.handle(response=response))
