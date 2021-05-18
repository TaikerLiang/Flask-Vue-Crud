from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_ets import MblRoutingRule
from test.spiders.terminal_ets import mbl


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=mbl, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,sys_no',
    [
        ('01_basic', 'EMCU5268400', '16701873'),
    ],
)
def test_main_page_handle(sub, container_no, sys_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = MblRoutingRule.build_request_option(container_no=container_no, sys_no=sys_no, sk='')

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MblRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
