from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_pct import SearchContainerRoutingRule
from test.spiders.terminal_pct import search_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,expect_exception',
    [
        ('e01_invalid_container_no', 'EMCU608509', TerminalInvalidContainerNoError),
    ],
)
def test_search_container_invalid_container_no_error(sub, container_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = SearchContainerRoutingRule.build_request_option(container_no=container_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
        ),
    )

    rule = SearchContainerRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
