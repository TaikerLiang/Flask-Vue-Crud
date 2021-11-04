from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        booking_no='',
        por=LocationItem(name='NANJING, JS, China'),
        pol=LocationItem(name='NANJING, JS, China'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA, USA'),
        etd=None,
        atd='2019/09/03 00:17',
        eta=None,
        ata='2019/09/26 13:48',
        firms_code=None,
        carrier_status='Steamship Release',
        carrier_release_date='2019/09/19 15:00',
        customs_release_status='Customs Release',
        customs_release_date='2019/09/23 16:05',
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='SEGU5613160',
        container_no='SEGU5613160',
        last_free_day=None,
        task_id=1,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=SEGU5613160&blno=W241061370&movertype=11&lifecycle=2'
    )

    assert results[7] == ContainerItem(
        container_key='YMLU8333608',
        container_no='YMLU8333608',
        last_free_day=None,
        task_id=1,
    )

    assert isinstance(results[8], RequestOption)
    assert results[8].url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=YMLU8333608&blno=W241061370&movertype=11&lifecycle=2'
    )
