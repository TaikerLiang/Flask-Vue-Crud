from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_ymlu_multi import MainInfoRoutingRule, HiddenFormSpec
from test.spiders.carrier_ymlu_multi import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_nos,task_ids',
    [
        ('01_all_exist', ['W216104890'], [1]),
        ('02_no_xta', ['W209047989'], [1]),
        ('03_no_release', ['I209365239'], [1]),
        ('04_multi_containers', ['W241061370'], [1]),
        ('05_with_firm_code', ['W226020752'], [1]),
        ('06_ip_blocked', ['E209048375'], [1]),
        ('07_delivery_without_time_status', ['W209139591'], [1]),
        ('08_to_be_advised_ver2', ['W470030608'], [1]),
        ('09_multi_mbl_nos', ['W216123181', 'W236958823', 'W240280894'], [1, 2, 3])
    ],
)
def test_main_info_routing_rule(sub, mbl_nos, task_ids, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = MainInfoRoutingRule.build_request_option(
        task_ids=task_ids,
        mbl_nos=mbl_nos,
        hidden_form_spec=HiddenFormSpec(view_state_generator='', view_state='', event_validation='', previous_page=''),
        captcha='',
        headers={},
    )

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = MainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

