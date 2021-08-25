from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oolu_multi import ContainerStatusRule
from test.spiders.carrier_oolu_multi import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,container_no',
    [
        ('01_first', '2109051600', 'OOLU9108987'),
        ('02_without_lfd_content', '2628633440', 'OOLU9077417'),
        ('03_without_lfd_title', '2631411950', 'OOLU1213862'),
    ],
)
def test_container_status_handler(sub, mbl_no, container_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = ContainerStatusRule.build_request_option(is_last=False, task_id=1, container_no=container_no, click_element_css='')

    response = TextResponse(
        url=option.url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    results = list(ContainerStatusRule._handle_response(task_id=1, response=response, container_no=container_no))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)