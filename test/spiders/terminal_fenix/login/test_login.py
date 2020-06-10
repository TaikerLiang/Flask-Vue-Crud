from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_fenix import LoginRoutingRule
from test.spiders.terminal_fenix import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,container_no,mbl_no', [
    ('01_only_container', 'CAIU7086501', ''),
    ('02_container_and_mbl_no', 'TCNU6056527', '2638732540')
])
def test_login_handle(sub, container_no, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = LoginRoutingRule.build_request_option(
        container_no=container_no, mbl_no=mbl_no
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta
        ),
    )

    rule = LoginRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

