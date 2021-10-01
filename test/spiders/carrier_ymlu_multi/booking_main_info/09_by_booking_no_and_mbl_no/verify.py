from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        booking_no='',
        por=LocationItem(name='SAINT PAUL, MN (USSXC)'),
        pol=LocationItem(name='SEATTLE, WA (USSEA)'),
        pod=LocationItem(name='PUSAN (KRPUS)'),
        place_of_deliv=LocationItem(name='AKITA (JPAXT)'),
        etd=None,
        atd='2021/07/19 15:36',
        eta=None,
        ata='2021/08/04 21:10',
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='SEGU1461135',
        container_no='SEGU1461135',
        last_free_day=None,
        task_id=1,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?'
        'var=6kXS94MAUKku1eUXw6LbZLq%2fhJoIqEkRm2PQOrN4ZqBGoYXmAJn6Idm02vkFT163PJ6F1zLlySfkmXJApabmtdDLZJ48zZWRq%2fNwH0pKx8XAlu0QNi0J8mxzbp%2bT1goZU8Kmmn2ldIC6bh0y2yhf%2bmx8ELlQNhIiESRUHYWyF4I%3d'
    )

    assert results[3] == ContainerItem(
        container_key='TCKU1188505',
        container_no='TCKU1188505',
        last_free_day=None,
        task_id=1,
    )
    assert isinstance(results[4], RequestOption)

    assert results[5] == ContainerItem(
        container_key='YMMU1150954',
        container_no='YMMU1150954',
        last_free_day=None,
        task_id=1,
    )
    assert isinstance(results[6], RequestOption)
