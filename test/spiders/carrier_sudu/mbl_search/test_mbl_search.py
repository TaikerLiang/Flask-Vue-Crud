from pathlib import Path
from queue import Queue

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_sudu import MblSearchResultRoutingRule, BasicRequestSpec, MblState, VoyageQueuePopper
from test.spiders.carrier_sudu import mbl_search
from test.spiders.carrier_sudu.mbl_search import queue_generator


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=mbl_search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,mbl_state',
    [
        ('01_single_container', 'SUDUN0498AQEP33P', MblState.FIRST),
        ('02_multiple_containers', 'SUDUN9998ALTNBPS', MblState.FIRST),
    ],
)
def test_mbl_search_result_handle_first(sub, mbl_no, mbl_state, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    option = MblSearchResultRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec, mbl_state=MblState.FIRST
    )

    response = TextResponse(
        url=option.url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'mbl_state': mbl_state,
            },
        ),
    )

    voyage_queue_popper = VoyageQueuePopper(Queue())
    routing_rule = MblSearchResultRoutingRule(voyage_queue_popper=voyage_queue_popper)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify_output(results=results)
    verify_module.verify_local_variable(routing_rule=routing_rule)


@pytest.mark.parametrize(
    'sub,mbl_no,mbl_state',
    [
        ('03_second_multiple_containers', 'SUDUN9998ALTNBPS', MblState.MULTIPLE),
    ],
)
def test_mbl_search_result_handle_multiple_without_voyage_queue(sub, mbl_no, mbl_state, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    option = MblSearchResultRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec, mbl_state=MblState.FIRST
    )

    response = TextResponse(
        url=option.url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'mbl_state': mbl_state,
            },
        ),
    )

    container_info = sample_loader.load_sample_module(sub, 'container_info')

    voyage_queue_popper = VoyageQueuePopper(Queue())
    routing_rule = MblSearchResultRoutingRule(voyage_queue_popper=voyage_queue_popper)
    routing_rule._containers_set = container_info.CONTAINER_SET
    routing_rule._container_link_element_map = container_info.CONTAINER_LINK_ELEMENT_MAP
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify_output(results=results)
    verify_module.verify_local_variable(routing_rule=routing_rule)


@pytest.mark.parametrize(
    'sub,mbl_no,mbl_state',
    [
        ('04_second_single_container', 'SUDUN0498AQEP33P', MblState.SINGLE),
        ('05_third_multiple_containers', 'SUDUN9998ALTNBPS', MblState.MULTIPLE),
    ],
)
def test_mbl_search_result_handle_with_voyage_queue(sub, mbl_no, mbl_state, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')
    fake_voyage_queue = queue_generator.get_queue_by_sub(sub=sub)

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    option = MblSearchResultRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec, mbl_state=MblState.FIRST
    )

    response = TextResponse(
        url=option.url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'mbl_state': mbl_state,
            },
        ),
    )

    voyage_queue_popper = VoyageQueuePopper(fake_voyage_queue)
    routing_rule = MblSearchResultRoutingRule(voyage_queue_popper=voyage_queue_popper)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,expect_exception',
    [
        ('e01_invalid_mbl_no', 'SUDUN9998ALTNBPU', CarrierInvalidMblNoError),
    ],
)
def test_mbl_search_result_handle_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    option = MblSearchResultRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec, mbl_state=MblState.FIRST
    )

    response = TextResponse(
        url=option.url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'mbl_state': MblState.FIRST,
            },
        ),
    )

    voyage_queue_popper = VoyageQueuePopper(Queue())
    routing_rule = MblSearchResultRoutingRule(voyage_queue_popper=voyage_queue_popper)

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
