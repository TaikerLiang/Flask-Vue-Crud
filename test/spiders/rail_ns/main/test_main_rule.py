from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.rail_ns import ContainerRoutingRule
from test.spiders.rail_ns import parse


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=parse, sample_path=sample_path)
    return sample_loader


# @pytest.mark.skip
@pytest.mark.parametrize(
    "sub",
    [
        ("01_basic"),
    ],
)
def test_track_and_trace_table_locator(sub, sample_loader):
    expected_rows = 7
    # arrange
    html_text = sample_loader.read_file(sub, "sample.html")
    container_nos = [
        "BSIU9806381",
        "GESU6668331",
        "OOLU6934706",
        "TCNU5503929",
        "CSLU1848046",
        "OOLU1759302",
        "KKFU7730014",
        "DFSU7363887",
        "TGBU5105859",
        "GLDU5327764",
        "NYKU0774449",
        "NYKU5127450",
        "SEGU4991972",
        "TRLU5925675",
        "TGBU3282876",
        "TEMU5131713",
        "TCNU4346450",
        "TGBU4361630",
        "GCXU5511599",
        "TCNU6553647",
    ]
    option = ContainerRoutingRule.build_request_option(container_nos=container_nos, proxy_manager=None)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    # action
    res = list(ContainerRoutingRule().handle(response=response))

    # assertion
    assert len(res) == expected_rows
