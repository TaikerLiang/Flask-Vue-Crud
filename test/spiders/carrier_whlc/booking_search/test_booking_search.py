from pathlib import Path
from test.spiders.carrier_whlc import booking_search

import pytest
from scrapy import Selector

from crawler.core.base_new import SEARCH_TYPE_CONTAINER
from crawler.spiders.carrier_whlc import BookingRoutingRule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,booking_no",
    [
        ("01_detail", "034B524357"),
    ],
)
def test_extract_basic_info(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, "detail_page.html")

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule(content_getter=None)
    results = routing_rule._extract_basic_info(response_selector)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify_basic(results=results)


@pytest.mark.parametrize(
    "sub,booking_no",
    [
        ("01_detail", "034B524357"),
    ],
)
def test_extract_vessel_info(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, "detail_page.html")

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule(content_getter=None)
    results = routing_rule._extract_vessel_info(response_selector)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify_vessel(results=results)


@pytest.mark.parametrize(
    "sub,booking_no",
    [
        ("01_detail", "034B524357"),
    ],
)
def test_extract_container_no_and_status_links(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, "detail_page.html")

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule(content_getter=None)
    results = list(routing_rule._extract_container_no_and_status_links(response_selector))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify_container_no(results=results)


@pytest.mark.parametrize(
    "sub,booking_no,container_no",
    [
        ("02_history", "034B524357", "TCKU7313477"),
    ],
)
def test_extract_container_status(sub, booking_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "history_page.html")
    info_pack = {
        "task_id": "1",
        "search_no": container_no,
        "search_type": SEARCH_TYPE_CONTAINER,
    }

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule(content_getter=None)
    results = list(routing_rule._extract_container_status(response=response_selector, info_pack=info_pack))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
