from pathlib import Path
from queue import Queue

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_sudu import BasicRequestSpec, ContainerDetailRoutingRule, MblState, VoyageQueuePusher
from test.spiders.carrier_sudu import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,mbl_state, container_link_element', [
    (
            '01_single_with_pol_pod',
            'SUDUN0NGB009496X',
            MblState.SINGLE,
            '',
    ),
    (
            '02_multiple_without_pol_pod',
            'SUDU20GUC000717X',
            MblState.MULTIPLE,
            'j_idt6:searchForm:j_idt24:j_idt27:0:contDetailsLink',
    ),
    (
            '03_multiple_with_voyage_spec_departure',
            'SUDUN9998ALTNBPS',
            MblState.MULTIPLE,
            'j_idt6:searchForm:j_idt24:j_idt27:1:contDetailsLink',
    ),
])
def test_container_handle(sub, mbl_no, mbl_state, container_link_element, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    voyage_info = sample_loader.load_sample_module(sub, 'voyage_info')
    voyage_spec = voyage_info.VOYAGE_SPEC

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    option = ContainerDetailRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec,
        container_link_element=container_link_element,
        mbl_state=mbl_state,
        voyage_spec=voyage_spec,
    )

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'container_key': container_link_element,
                'mbl_state': mbl_state,
                'voyage_spec': voyage_spec,
            }
        )
    )

    voyage_queue = Queue()
    routing_rule = ContainerDetailRoutingRule(VoyageQueuePusher(voyage_queue))
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results, queue=voyage_queue)
