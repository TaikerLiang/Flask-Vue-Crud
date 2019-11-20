from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_aplu_cmdu_anlc import SharedUrlFactory, UrlSpec, RoutingManager, CarrierAnlcSpider
from test.spiders.carrier_aplu_cmdu_anlc.anlc import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_not_finish', 'AWT0143054'),
    ('02_finish', 'AWT0143291'),
    ('03_multiple_containers', 'AWT0143454'),
    ('04_pod_status_is_remaining', 'AWT0143370'),
])
def test_parse(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    url_factory = SharedUrlFactory(home_url=CarrierAnlcSpider.home_url, mbl_no=mbl_no)
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

    spider = CarrierAnlcSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'AWT0143111', CarrierInvalidMblNoError),
])
def test_parse_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    url_factory = SharedUrlFactory(home_url=CarrierAnlcSpider.home_url, mbl_no=mbl_no)
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

    spider = CarrierAnlcSpider(name=None, mbl_no=mbl_no)

    with pytest.raises(expect_exception):
        spider.parse(response)
