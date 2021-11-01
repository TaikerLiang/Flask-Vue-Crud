from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.scspa_share_spider import ContentGetter
from test.spiders.terminal_scspa_north_charleston import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        ("01_basic", ["FCIU9155148", "FSCU8053140", "HDMU4748456", "TCNU7907787"]),
    ],
)
def test_content_getter_extract(sub, container_no_list, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    response = TextResponse(
        url="www.google.com",
        body=httptext,
        encoding="utf-8",
    )
    getter = ContentGetter()
    results = getter.extract(page_source=httptext)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
