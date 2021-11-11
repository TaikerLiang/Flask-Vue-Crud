from pathlib import Path
import pytest

from scrapy import Request
from scrapy.http import TextResponse

from src.crawler.core_terminal.gpa_share_spider import ContainerRoutingRule
from test.spiders.terminal_gpa_garden_city_l737 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        (
            "01_basic",
            [
                "OOLU8981883",
                "CAIU3803055",
                "CMAU0101886",
                "TRLU8224030",
                "FCIU6164362",
            ],
        )
    ],
)
def test_container_handle(sub, container_no_list, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        container_no_list=container_no_list,
        cookies={},
    )
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = ContainerRoutingRule()
    results_dict = {item.get("container_no"): item for item in rule.handle(response=response)}

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results_dict)


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        (
            "e01_invalid_container_no",
            [
                "QQQQQQQQQQQQ",
            ],
        )
    ],
)
def test_invalid_container_no(sub, container_no_list, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        container_no_list=container_no_list,
        cookies={},
    )
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = ContainerRoutingRule()
    results = [item for item in rule.handle(response=response)]

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        (
            "e02_invalid_data_field",
            [
                "OOLU8981883",
                "CAIU3803055",
                "CMAU0101886",
            ],
        )
    ],
)
def test_container_check_data_validability(sub, container_no_list, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        container_no_list=container_no_list,
        cookies={},
    )
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = ContainerRoutingRule()
    results_dict = {item.get("container_no"): item for item in rule.handle(response=response)}

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results_dict)
