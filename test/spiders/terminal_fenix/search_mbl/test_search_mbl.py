from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse, HtmlResponse

from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.spiders.terminal_fenix import SearchMblRoutingRule
from test.spiders.terminal_fenix import search_mbl


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_mbl, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_without_freight_release', '2638732540'),
    ('02_with_freight_release', '146000297601'),
])
def test_search_mbl_handle(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = SearchMblRoutingRule.build_request_option(
        mbl_no=mbl_no, token=''
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
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


@pytest.mark.parametrize('sub,mbl_no,status_code', [
    ('w01_invalid_mbl_no', '263873254', 404),
])
def test_search_mbl_handle_warning(sub, mbl_no, status_code, sample_loader):
    option = SearchMblRoutingRule.build_request_option(
        mbl_no=mbl_no, token=''
    )

    response = HtmlResponse(
        status=status_code,
        url=option.url,
        body='',
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


@pytest.mark.parametrize('sub,mbl_no,expected_exception', [
    ('e01_unexpected_format', '146000297601', TerminalResponseFormatError),
])
def test_search_mbl_handle_error(sub, mbl_no, expected_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = SearchMblRoutingRule.build_request_option(
        mbl_no=mbl_no, token=''
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchMblRoutingRule()
    with pytest.raises(expected_exception):
        list(rule.handle(response=response))

