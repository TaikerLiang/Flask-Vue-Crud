from pathlib import Path
from test.spiders.carrier_whlc import mbl_search

import pytest
from scrapy import Selector

from crawler.core.base_new import SEARCH_TYPE_CONTAINER
from crawler.spiders.carrier_whlc import MblRoutingRule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=mbl_search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_single_container", "031B554489"),
        ("02_multiple_container", "025B648783"),
    ],
)
def test_extract_container_info(sub, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, "main_page.html")

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule(content_getter=None)
    results = list(routing_rule._extract_container_info(response_selector, info_pack={}))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("03_detail", "031B554489", "WHSU6570305"),
    ],
)
def test_extract_date_information(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "detail_page.html")
    info_pack = {
        "task_id": "1",
        "search_no": container_no,
        "search_type": SEARCH_TYPE_CONTAINER,
    }

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule(content_getter=None)
    results = routing_rule._extract_date_information(response=response_selector, info_pack=info_pack)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("04_history", "031B554489", "WHSU6570305"),
    ],
)
def test_extract_container_status(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "history_page.html")
    info_pack = {
        "task_id": "1",
        "search_no": container_no,
        "search_type": SEARCH_TYPE_CONTAINER,
    }

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule(content_getter=None)
    results = list(routing_rule._extract_container_status(response=response_selector, info_pack=info_pack))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
