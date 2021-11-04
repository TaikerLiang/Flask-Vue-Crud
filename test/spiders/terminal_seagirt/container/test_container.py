from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_seagirt import ContainerRoutingRule
from test.spiders.terminal_seagirt import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no',
    [
        ('01_basic', 'DRYU2659319'),
        ('02_data_not_found', 'EISU3920168'),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerRoutingRule.build_request_option(container_nos=[container_no])

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'container_nos': [container_no],
            }
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
