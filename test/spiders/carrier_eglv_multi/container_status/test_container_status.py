from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv_multi import ContainerStatusRoutingRule
from test.spiders.carrier_eglv_multi import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("01_single_table", "003902245109", "HMCU9173542"),
        ("02_two_table", "003902385989", "EITU1673822"),
    ],
)
def test_container_status_handler(sub, mbl_no, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContainerStatusRoutingRule.build_request_option(
        task_id="1",
        search_no=mbl_no,
        container_no=container_no,
        onboard_date="",
        pol="",
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
