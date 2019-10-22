from typing import List

import scrapy

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest
from test.spiders.utils import extract_url_from


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W202119769',
        por=LocationItem(name='TAOYUAN, Taiwan'),
        pol=LocationItem(name='KEELUNG, Taiwan'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA, USA'),
        etd=None,
        atd='2019/08/15 04:00',
        eta=None,
        ata='2019/08/26 13:48',
        firms_code='Y773',
        carrier_status='Steamship Release',
        carrier_release_date='2019/08/20 19:30',
        customs_release_status='Customs Release',
        customs_release_date='2019/08/23 13:40',
    )

    assert results[1] == ContainerItem(
        container_key='YMMU4042547',
        container_no='YMMU4042547',
        last_free_day=None,
    )

    assert isinstance(results[2], scrapy.Request)
    assert results[2].url == 'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?' \
                             'rdolType=BL&ctnrno=YMMU4042547&blno=W202119769&movertype=11&lifecycle=1'

