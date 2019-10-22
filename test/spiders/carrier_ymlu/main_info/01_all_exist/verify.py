from typing import List

import scrapy

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest
from test.spiders.utils import extract_url_from


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W209131160',
        por=LocationItem(name='KAOHSIUNG, Taiwan'),
        pol=LocationItem(name='KAOHSIUNG, Taiwan'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='DALLAS, TX, USA'),
        etd=None,
        atd='2019/08/06 13:00',
        eta=None,
        ata='2019/08/20 13:57',
        firms_code='Y773',
        carrier_status='Steamship Release',
        carrier_release_date='2019/08/26 16:09',
        customs_release_status='Customs Release',
        customs_release_date='2019/08/26 23:45',
    )

    assert results[1] == ContainerItem(
        container_key='YMLU3555177',
        container_no='YMLU3555177',
        last_free_day='2019/08/29',
    )

    assert isinstance(results[2], scrapy.Request)
    assert results[2].url == 'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?' \
                             'rdolType=BL&ctnrno=YMLU3555177&blno=W209131160&movertype=31&lifecycle=2'

