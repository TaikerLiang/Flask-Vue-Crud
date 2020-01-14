from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='E491301617',
        por=LocationItem(name='HAIPHONG, Vietnam'),
        pol=LocationItem(name='HAIPHONG, Vietnam'),
        pod=LocationItem(name='SAVANNAH, GA, USA'),
        place_of_deliv=LocationItem(name='ATLANTA, GA, USA'),
        etd=None,
        atd='2019/09/16 18:30',
        eta='2019/10/23 12:00',
        ata=None,
        firms_code='L738',
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
    )

    assert results[1] == ContainerItem(
        container_key='YMMU6043861',
        container_no='YMMU6043861',
        last_free_day=None,
    )

    assert isinstance(results[2], RoutingRequest)
    assert results[2].request.url == (
        'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?'
        'rdolType=BL&ctnrno=YMMU6043861&blno=E491301617&movertype=11&lifecycle=1'
    )

