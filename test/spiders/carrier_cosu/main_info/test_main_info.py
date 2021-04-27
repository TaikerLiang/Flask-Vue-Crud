from pathlib import Path
from typing import List

import pytest
from scrapy import Selector

from crawler.spiders.carrier_cosu import MainInfoRoutingRule, ItemExtractor

from test.spiders.carrier_cosu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,make_item_fun', [
    ('01_main_item', '6199589860', ItemExtractor._make_main_item),
    ('02_vessel_items', '6300090760', ItemExtractor._make_vessel_items),
    ('03_container_items', '6283228140', ItemExtractor._make_container_items),
])
def test_main_info(sample_loader, sub, mbl_no, make_item_fun):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    result = make_item_fun(response=resp)

    # assert
    if isinstance(result, List):
        verify_module = sample_loader.load_sample_module(sub, 'verify')
        verify_module.verify(items=result)
    else:
        verify_module = sample_loader.load_sample_module(sub, 'verify')
        verify_module.verify(item=result)


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('04_container_status_items', '6283228140', 'CSNU6395607'),
])
def test_main_info_container_status(sample_loader, sub, mbl_no, container_no):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    items = ItemExtractor._make_container_status_items(container_no=container_no, response=resp)

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(items=items)


@pytest.mark.parametrize('sub,mbl_no', [
    ('e01_invalid_mbl_no', '6213846642'),
])
def test_main_info_no_invalid(sample_loader, sub, mbl_no):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    rule = MainInfoRoutingRule(content_getter=None)
    result = rule._is_mbl_no_invalid(response=resp)

    # assert
    assert result is True

