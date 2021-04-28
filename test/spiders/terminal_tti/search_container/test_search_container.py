from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_tti import SearchContainerRoutingRule
from test.spiders.terminal_tti import search_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub, container_no', [
    ('01_no_lfd', 'MSDU7965509'),
    ('02_with_lfd', 'CAAU5077128'),
    ('03_tmf_and_diff_freight', 'HASU4204375'),
    ('04_demurrage_and_paid', 'MSDU1314937'),
])
def test_search_container_handle(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = SearchContainerRoutingRule.build_request_option(container_no=container_no)
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub, container_no, expected_exception', [
    ('e01_invalid_container_no', 'MSDU732250', TerminalInvalidContainerNoError),
])
def test_search_container_handle_error(sub, container_no, expected_exception, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = SearchContainerRoutingRule.build_request_option(container_no=container_no)
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchContainerRoutingRule()
    with pytest.raises(expected_exception=expected_exception):
        list(rule.handle(response=response))



