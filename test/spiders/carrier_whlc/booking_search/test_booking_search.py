from pathlib import Path

import pytest
from scrapy import Selector

from crawler.spiders.carrier_whlc import BookingRoutingRule
from test.spiders.carrier_whlc import booking_search


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,booking_no',
    [
        ('01_detail', '034B524357'),
    ],
)
def test_extract_basic_info(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'detail_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule()
    results = routing_rule._extract_basic_info(response_selector)

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify_basic(results=results)


@pytest.mark.parametrize(
    'sub,booking_no',
    [
        ('01_detail', '034B524357'),
    ],
)
def test_extract_vessel_info(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'detail_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule()
    results = routing_rule._extract_vessel_info(response_selector)

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify_vessel(results=results)


@pytest.mark.parametrize(
    'sub,booking_no',
    [
        ('01_detail', '034B524357'),
    ],
)
def test_extract_container_no_and_status_links(sub, booking_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'detail_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule()
    results = list(routing_rule._extract_container_no_and_status_links(response_selector))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify_container_no(results=results)


@pytest.mark.parametrize(
    'sub,booking_no,container_no',
    [
        ('02_history', '034B524357', 'TCKU7313477'),
    ],
)
def test_extract_container_status(sub, booking_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'history_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = BookingRoutingRule()
    results = list(routing_rule._extract_container_status(response_selector))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)