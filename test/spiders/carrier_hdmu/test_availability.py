from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.items import ContainerItem
from crawler.spiders.carrier_hdmu import CarrierHdmuSpider, UrlFactory
from test.spiders.carrier_hdmu import samples_availability

SAMPLE_PATH = Path('./samples_availability/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_availability'
    sample_loader.setup(sample_package=samples_availability, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no, container_item', [
    ('01_first', 'TAWB0789799',
     ContainerItem(
         container_no='CAIU7479659',
         last_free_day='Gated-out',
         mt_location='M&N EQUIPMENT SERVICES ( EMPTIES ONLY) (MINNEAPOLIS, MN)',
         det_free_time_exp_date='09-May-2019',
         por_etd=None,
         pol_eta=None,
         final_dest_eta=None,
         ready_for_pick_up=None,
        ),
     ),
])
def test_parse_availability(sample_loader, sub, mbl_no, container_item):

    main_html_file = str(sample_loader.build_file_path(sub, f'ava_{mbl_no}.html'))
    with open(main_html_file, 'r', encoding="utf-8") as fp:
        httptext = fp.read()

    make_url = UrlFactory()
    url = make_url.build_availability_url()

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=httptext,
        request=Request(
            url=url,
            meta={'container_item': container_item},
        )
    )

    spider = CarrierHdmuSpider(name=None, mbl_no=mbl_no)
    result = list(spider.parse_availability(response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_availability')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(result=result)

    pass
