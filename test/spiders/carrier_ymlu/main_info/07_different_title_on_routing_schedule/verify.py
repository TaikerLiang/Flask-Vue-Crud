from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W125326102',
        por=LocationItem(name='SHREVEPORT, LA, USA'),
        pol=LocationItem(name='LONG BEACH, CA, USA'),
        pod=LocationItem(name='QINGDAO, SD, China'),
        place_of_deliv=LocationItem(name='QINGDAO, SD, China'),
        etd='2019/10/27 03:00',
        atd=None,
        eta=None,
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
    )

    assert results[1] == ContainerItem(
        container_key='OCGU8024931',
        container_no='OCGU8024931',
        last_free_day=None,
    )

    assert isinstance(results[2], RoutingRequest)
    assert results[2].request.url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=OCGU8024931&blno=W125326102&movertype=11&lifecycle=1'
    )

    assert results[3] == ContainerItem(
        container_key='TEMU7059599',
        container_no='TEMU7059599',
        last_free_day=None,
    )

    assert isinstance(results[4], RoutingRequest)
    assert results[4].request.url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=TEMU7059599&blno=W125326102&movertype=11&lifecycle=1'
    )

