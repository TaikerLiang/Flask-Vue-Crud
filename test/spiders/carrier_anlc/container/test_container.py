from pathlib import Path
from test.spiders.carrier_anlc import container

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.anlc_aplu_cmdu_share_spider import (
    ContainerStatusRoutingRule as MultiContainerStatusRoutingRule,
)
from crawler.spiders.carrier_anlc_aplu_cmdu import ContainerStatusRoutingRule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("01_basic", "QDGA385860", "APZU4632334"),
    ],
)
def test_container_status_routing_rule(sample_loader, sub, mbl_no, container_no):
    html_text = sample_loader.read_file(sub, "container.html")

    option = ContainerStatusRoutingRule.build_request_option(container_no=container_no, search_no=mbl_no)

    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = ContainerStatusRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("01_basic", "QDGA385860", "APZU4632334"),
    ],
)
def test_multi_container_status_routing_rule(sample_loader, sub, mbl_no, container_no):
    html_text = sample_loader.read_file(sub, "container.html")

    option = MultiContainerStatusRoutingRule.build_request_option(
        container_no=container_no,
        search_no=mbl_no,
        task_id=1,
    )

    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MultiContainerStatusRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.multi_verify(results=results)
