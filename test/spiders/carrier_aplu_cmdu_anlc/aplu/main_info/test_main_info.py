from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_aplu_cmdu_anlc import UrlSpec, CarrierApluSpider, RoutingManager, SharedUrlFactory
from test.spiders.carrier_aplu_cmdu_anlc.aplu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_not_finish', 'AXK0185154'),
    ('02_finish', 'XHMN810789'),
    ('03_multiple_containers', 'SHSE015942'),
    ('04_por_dest', 'AWB0135426'),
    ('05_pod_status_is_remaining', 'NANZ001007'),
])
def test_parse(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    url_factory = SharedUrlFactory(home_url=CarrierApluSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_bill_url_builder()
    url = url_builder.build_url_from_spec(spec=UrlSpec())

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={RoutingManager.META_ROUTING_RULE: 'HANDLE_FIRST_TIER'}
        )
    )

    spider = CarrierApluSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'XHMN810788', CarrierInvalidMblNoError),
])
def test_parse_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    url_factory = SharedUrlFactory(home_url=CarrierApluSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_bill_url_builder()
    url = url_builder.build_url_from_spec(spec=UrlSpec())

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={RoutingManager.META_ROUTING_RULE: 'HANDLE_FIRST_TIER'}
        ),
    )

    spider = CarrierApluSpider(name=None, mbl_no=mbl_no)

    with pytest.raises(expect_exception):
        spider.parse(response)
