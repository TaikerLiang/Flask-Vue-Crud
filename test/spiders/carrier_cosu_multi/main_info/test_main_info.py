from pathlib import Path
from typing import List

import pytest
from scrapy import Selector

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.spiders.carrier_cosu_multi import MainInfoRoutingRule, ItemExtractor

from test.spiders.carrier_cosu_multi import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader



@pytest.mark.parametrize(
    'sub,mbl_no,task_id,make_item_fun',
    [
        ('01_main_item', '6199589860', '1', ItemExtractor._make_main_item),
        ('02_vessel_items', '6300090760', '2', ItemExtractor._make_vessel_items),
        ('03_container_items', '6283228140', '3', ItemExtractor._make_container_items),
    ],
)
def test_main_info(sample_loader, sub, mbl_no, task_id, make_item_fun):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    if make_item_fun == ItemExtractor._make_main_item:
        result = make_item_fun(response=resp, search_type=SHIPMENT_TYPE_MBL, task_id=task_id)
    else:
        result = make_item_fun(response=resp, task_id=task_id)

    # assert
    if isinstance(result, List):
        verify_module = sample_loader.load_sample_module(sub, 'verify')
        verify_module.verify(items=result)
    else:
        verify_module = sample_loader.load_sample_module(sub, 'verify')
        verify_module.verify(item=result)


@pytest.mark.parametrize(
    'sub,mbl_no,task_id,container_no',
    [
        ('04_container_status_items', '6283228140', '4', 'CSNU6395607'),
    ],
)
def test_main_info_container_status(sample_loader, sub, mbl_no, task_id, container_no):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    items = ItemExtractor._make_container_status_items(container_no=container_no, response=resp, task_id=task_id)

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(items=items)


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('e01_invalid_mbl_no', '6213846642'),
    ],
)
def test_main_info_no_invalid(sample_loader, sub, mbl_no):
    http_text = sample_loader.read_file(sub, 'sample.html')

    resp = Selector(text=http_text)

    # action
    rule = MainInfoRoutingRule()
    result = rule._is_mbl_no_invalid(response=resp)

    # assert
    assert result is True