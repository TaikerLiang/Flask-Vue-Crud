from pathlib import Path

import pytest
from scrapy import Selector

from crawler.spiders.carrier_whlc import MblRoutingRule
from test.spiders.carrier_whlc import mbl_search


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=mbl_search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('01_single_container', '031B554489'),
        ('02_multiple_container', '025B648783'),
    ],
)
def test_extract_container_info(sub, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'main_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule()
    results = list(routing_rule._extract_container_info(response_selector))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,container_no',
    [
        ('03_detail', '031B554489', 'WHSU6570305'),
    ],
)
def test_extract_date_information(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'detail_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule()
    results = routing_rule._extract_date_information(response_selector)

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,container_no',
    [
        ('04_history', '031B554489', 'WHSU6570305'),
    ],
)
def test_extract_container_status(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'history_page.html')

    response_selector = Selector(text=html_text)

    routing_rule = MblRoutingRule()
    results = list(routing_rule._extract_container_status(response_selector))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)