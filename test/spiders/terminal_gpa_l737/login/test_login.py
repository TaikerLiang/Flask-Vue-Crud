from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import LoginNotSuccessFatal
from crawler.core_terminal.gpa_share_spider import LoginRoutingRule
from test.spiders.terminal_gpa_l737 import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        ("e01_login_fail", ["BEAU6310891"]),
    ],
)
def test_login_fail(sub, container_no_list, sample_loader):
    expected_exception = LoginNotSuccessFatal

    # arrange
    http_text = sample_loader.read_file(sub, "sample.html")

    option = LoginRoutingRule.build_request_option(container_no_list=container_no_list)
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = LoginRoutingRule()

    # action
    # assert
    with pytest.raises(expected_exception):
        rule._raise_if_login_fail(page=http_text)
