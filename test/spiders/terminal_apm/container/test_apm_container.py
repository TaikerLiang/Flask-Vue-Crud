from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_apm import ContainerRoutingRule, TerminalApmLASpider
from test.spiders.terminal_apm import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,terminal_id',
    [
        ('01', 'EISU9133920', TerminalApmLASpider.terminal_id),
        ('02_holds_empty', 'EGHU9572519', TerminalApmLASpider.terminal_id),
        ('03_lfd_exist', 'EGHU9427104', TerminalApmLASpider.terminal_id),
    ],
)
def test_container_handle(sub, container_no, terminal_id, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerRoutingRule.build_request_option(container_no=container_no, terminal_id=terminal_id)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,terminal_id,expect_exception',
    [
        ('e01_no_result', 'EISU9133921', 'c56ab48b-586f-4fd2-9a1f-06721c94f3bb', TerminalInvalidContainerNoError),
    ],
)
def test_container_handle_container_error(sub, container_no, terminal_id, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerRoutingRule.build_request_option(container_no=container_no, terminal_id=terminal_id)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    rule = ContainerRoutingRule()

    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
