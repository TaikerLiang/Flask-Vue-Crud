from pathlib import Path
from test.spiders.carrier_cosu import main_info
from typing import List

import pytest
from scrapy import Selector

from crawler.core.base_new import SEARCH_TYPE_MBL
from crawler.spiders.carrier_cosu import ItemExtractor, MainInfoRoutingRule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,make_item_fun",
    [
        ("01_main_item", ItemExtractor()._make_main_item),
        ("02_vessel_items", ItemExtractor()._make_vessel_items),
        ("03_container_items", ItemExtractor()._make_container_items),
    ],
)
def test_main_info(sample_loader, sub, make_item_fun):
    http_text = sample_loader.read_file(sub, "sample.html")

    resp = Selector(text=http_text)

    # action
    if sub == "01_main_item":
        result = make_item_fun(response=resp, search_type=SEARCH_TYPE_MBL)
    else:
        result = make_item_fun(response=resp)

    # assert
    if isinstance(result, List):
        verify_module = sample_loader.load_sample_module(sub, "verify")
        verify_module.verify(items=result)
    else:
        verify_module = sample_loader.load_sample_module(sub, "verify")
        verify_module.verify(item=result)


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("04_container_status_items", "CSNU6395607"),
    ],
)
def test_main_info_container_status(sample_loader, sub, container_no):
    http_text = sample_loader.read_file(sub, "sample.html")

    resp = Selector(text=http_text)

    # action
    items = ItemExtractor()._make_container_status_items(container_no=container_no, response=resp)

    # assert
    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(items=items)


@pytest.mark.parametrize(
    "sub",
    [
        ("05_railway_info"),
    ],
)
def test_main_info_railway_info(sample_loader, sub):
    http_text = sample_loader.read_file(sub, "sample.html")

    resp = Selector(text=http_text)

    # action
    result = ItemExtractor()._extract_railway_info(response=resp)

    # assert
    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(item=result)


@pytest.mark.parametrize(
    "sub",
    [
        ("e01_invalid_mbl_no"),
    ],
)
def test_main_info_no_invalid(sample_loader, sub):
    http_text = sample_loader.read_file(sub, "sample.html")

    resp = Selector(text=http_text)

    # action
    rule = MainInfoRoutingRule(content_getter=None)
    result = rule._is_mbl_no_invalid(response=resp)

    # assert
    assert result is True
