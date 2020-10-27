from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidMblNoError
from crawler.spiders.terminal_tti import SearchMblRoutingRule
from test.spiders.terminal_tti import search_mbl


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_mbl, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub, mbl_no', [
    ('01_basic', 'MEDUQ3514583'),
])
def test_search_mbl_handle(sub, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = SearchMblRoutingRule.build_request_option(mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchMblRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub, mbl_no, expected_exception', [
    ('e01_invalid_mbl_no', 'SUDUN0KSZ075516X', TerminalInvalidMblNoError),
])
def test_search_mbl_handle_error(sub, mbl_no, expected_exception, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = SearchMblRoutingRule.build_request_option(mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchMblRoutingRule()
    with pytest.raises(expected_exception=expected_exception):
        list(rule.handle(response=response))



