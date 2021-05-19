from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_tos import MblDetailRoutingRule
from test.spiders.terminal_tos import mbl_detail


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=mbl_detail, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,',
    [
        ('01_basic', 'YMLUW202129800'),
    ],
)
def test_mbl_detail_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = MblDetailRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={'mbl_no': mbl_no},
        ),
    )

    rule = MblDetailRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('w01_invalid_mbl_no', 'YMLUW2021298'),
    ],
)
def test_mbl_detail_handle_warning(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = MblDetailRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={'mbl_no': mbl_no},
        ),
    )

    rule = MblDetailRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
