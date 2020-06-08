from pathlib import Path

import pytest
from scrapy.http import TextResponse

from crawler.spiders.vessel_big_schedules import VesselScheduleRoutingRule
from test.spiders.vessel_big_schedules import port_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=port_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,scac,vessel_name,carrier_id,vessel_gid', [
    ('01_basic', 'COSU', 'CMA CGM FIDELIO', '2', 'V000001036'),
])
def test_vessel_schedule_routing_rule(sub, scac, vessel_name, carrier_id, vessel_gid, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    cookie = {}
    option = VesselScheduleRoutingRule.build_request_option(
        scac=scac, vessel_name=vessel_name, carrier_id=carrier_id, vessel_gid=vessel_gid, cookie=cookie)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=json_text,
        headers={
            'accept': "application/json, text/plain, */*",
            'sec-fetch-dest': "empty",
        },
    )

    rule = VesselScheduleRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
