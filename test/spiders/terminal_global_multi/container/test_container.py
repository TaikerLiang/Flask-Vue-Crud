from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.spiders.terminal_global_multi import ContainerRoutingRule
from test.spiders.terminal_global_multi import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,',
    [
        ('01_basic', 'KKFU7634200'),
    ],
)
def test_container_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,invalid_no_item',
    [
        ('e01_invalid_container_no', 'TGBU678745', InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    assert list(rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
