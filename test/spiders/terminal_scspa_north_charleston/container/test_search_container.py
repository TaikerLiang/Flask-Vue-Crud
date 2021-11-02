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
    "sub",
    [
        ("01_basic"),
    ],
)
def test_content_getter_extract(sub, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    getter = ContentGetter()
    results = getter.extract(page_source=httptext)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
