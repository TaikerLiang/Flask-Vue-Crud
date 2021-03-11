from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_sudu import BasicRequestSpec, VoyageRoutingRule, VoyageSpec, MblState
from test.spiders.carrier_sudu import voyage_routing


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=voyage_routing, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,voyage_location, voyage_direction', [
    ('01_pol', 'SUDUN9998ALTNBPS', 'Shanghai CNSHA', 'Departure'),
    ('02_pod', 'SUDUN9998ALTNBPS', 'Houston USHOU', 'Arrival'),
    ('03_no_info', 'SUDUN0SHA109846X', 'Los Angeles USLAX', 'Arrival'),
])
def test_voyage_routing_rule(sub, mbl_no, voyage_location, voyage_direction, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    voyage_spec = VoyageSpec(
        direction=voyage_direction, container_key='', voyage_key='', location=voyage_location, container_no='')
    option = VoyageRoutingRule.build_request_option(
        basic_request_spec=basic_request_spec, voyage_spec=voyage_spec, mbl_state=MblState.SINGLE
    )

    response = TextResponse(
        url=option.url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
            # meta={
            #     'mbl_no': mbl_no,
            #     'mbl_state': MblState.SINGLE,
            #     'voyage_location': voyage_location,
            #     'voyage_direction': voyage_direction,
            #     'basic_request_spec': basic_request_spec,
            # }
        )
    )

    routing_rule = VoyageRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
