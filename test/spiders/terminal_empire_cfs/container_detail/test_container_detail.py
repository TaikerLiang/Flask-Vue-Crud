from pathlib import Path

import pytest
from scrapy.http import TextResponse

from crawler.spiders.terminal_empire_cfs import ContainerDetailRoutingRule
from test.spiders.terminal_empire_cfs import container_detail


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_detail, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,href",
    [
        ("01_basic", "MATU4547183", "details.jsp?code=EMP&link=I26961"),
        ("02_no_last_free_day", "CAIU7902626", "details.jsp?code=EMP&link=I27395"),
    ],
)
def test_container_handle(sub, container_no, href, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerDetailRoutingRule.build_request_option(container_no=container_no, href=href)

    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
    )

    rule = ContainerDetailRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
