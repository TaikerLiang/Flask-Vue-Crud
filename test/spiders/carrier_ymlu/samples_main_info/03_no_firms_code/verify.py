from typing import List

import scrapy

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest
from test.spiders.utils import extract_url_from


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W202119210',
        por=LocationItem(name='TAOYUAN, Taiwan'),
        pol=LocationItem(name='KAOHSIUNG, Taiwan'),
        pod=LocationItem(name='TACOMA, WA, USA'),
        place_of_deliv=LocationItem(name='TACOMA, WA, USA'),
        etd=None,
        atd='2019/08/31 21:00',
        eta=None,
        ata='2019/09/15 09:00',
        firms_code=None,
        carrier_status='Steamship Release',
        carrier_release_date='2019/09/09 03:17',
        customs_release_status='Customs Release',
        customs_release_date='2019/09/11 14:05',
    )

    assert results[1] == ContainerItem(
        container_key='YMLU9512450',
        container_no='YMLU9512450',
        last_free_day='2019/09/23',
    )

    assert isinstance(results[2], scrapy.Request)
    assert results[2].url == 'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?' \
                             'rdolType=BL&ctnrno=YMLU9512450&blno=W202119210&movertype=11&lifecycle=1'

