from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_fenix import ListTracedContainerRoutingRule
from test.spiders.terminal_fenix import listed_traced_containers


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=listed_traced_containers, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,is_first',
    [
        ('01_first_and_exist', 'TCNU6056527', True),
        ('02_first_and_not_exist', 'EITU1651783', True),
        ('03_not_first_and_exist', 'CAIU7086501', False),
    ],
)
def test_container_handle(sub, container_no, is_first, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ListTracedContainerRoutingRule.build_request_option(
        container_no=container_no, authorization_token='', is_first=is_first
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'is_first': is_first,
                'container_no': container_no,
                'authorization_token': '',
            },
        ),
    )

    rule = ListTracedContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
