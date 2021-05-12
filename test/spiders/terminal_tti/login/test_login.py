from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_tti import LoginRoutingRule
from test.spiders.terminal_tti import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub, container_no, mbl_no',
    [
        ('01_both', 'FFAU1729638', 'MEDUN8495321'),
        ('02_only_container', 'TGHU8593471', ''),
    ],
)
def test_search_mbl_handle(sub, container_no, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = LoginRoutingRule.build_request_option(container_no=container_no, mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = LoginRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
