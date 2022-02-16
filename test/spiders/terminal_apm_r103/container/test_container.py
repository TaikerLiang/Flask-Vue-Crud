from pathlib import Path
from test.spiders.terminal_apm_r103 import container

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.apm_share_spider import ContainerRoutingRule
from crawler.spiders.terminal_apm_r103 import TerminalApmMBSpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,terminal_id,data_source_id",
    [
        ("01", "FCIU3460294", TerminalApmMBSpider.terminal_id, TerminalApmMBSpider.data_source_id),
        ("02_holds_empty", "UACU5946066", TerminalApmMBSpider.terminal_id, TerminalApmMBSpider.data_source_id),
        ("03_lfd_exist", "KOCU4471983", TerminalApmMBSpider.terminal_id, TerminalApmMBSpider.data_source_id),
        ("04_data_not_found", "KOCU9871987", TerminalApmMBSpider.terminal_id, TerminalApmMBSpider.data_source_id),
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
                "data_source_id": "070b73a5-7290-439c-94f2-aa8168d76780",
            },
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
