from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_ets import ContainerRoutingRule
from test.spiders.terminal_ets import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_without_demurrage', 'EISU8049563'),
        ('02_with_demurrage_appointment', 'EMCU5268400'),
        ('03_diff_customs_release', 'EITU1162062'),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerRoutingRule.build_request_option(
        container_no_list=[container_no],
        sk=''
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

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
