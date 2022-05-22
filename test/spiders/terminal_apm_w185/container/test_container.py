from pathlib import Path
from test.spiders.terminal_apm_w185 import container

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.apm_share_spider import ContainerRoutingRule
from crawler.spiders.terminal_apm_w185 import TerminalApmLASpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,terminal_id,data_source_id",
    [
        ("01", "TCNU1654552", TerminalApmLASpider.terminal_id, TerminalApmLASpider.data_source_id),
        ("02_holds_empty", "EISU9112296", TerminalApmLASpider.terminal_id, TerminalApmLASpider.data_source_id),
        ("03_lfd_exist", "SEGU5842736", TerminalApmLASpider.terminal_id, TerminalApmLASpider.data_source_id),
        ("04_data_not_found", "EISU9133921", TerminalApmLASpider.terminal_id, TerminalApmLASpider.data_source_id),
    ],
)
def test_container_handle(sub, container_no, terminal_id, data_source_id, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = ContainerRoutingRule.build_request_option(
        container_nos=[container_no], terminal_id=terminal_id, data_source_id=data_source_id
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "container_nos": [container_no],
                "terminal_id": "cfc387ee-e47e-400a-80c5-85d4316f1af9",
                "data_source_id": "73067122-4bdb-4912-b6c7-4e3cb5777eaf",
            },
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
