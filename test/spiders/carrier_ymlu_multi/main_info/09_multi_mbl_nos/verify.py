from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem, ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W216123181',
        por=LocationItem(name='TAICHUNG (TWTXG)'),
        pol=LocationItem(name='KAOHSIUNG (TWKHH)'),
        pod=LocationItem(name='LOS ANGELES, CA (USLAX)'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA (USLAX)'),
        etd=None,
        atd='2021/07/31 13:30',
        eta=None,
        ata=None,
        firms_code='Y773',
        carrier_status='Steamship Release',
        carrier_release_date='2021/08/10 14:54',
        customs_release_status='(not yet Customs Release)',
        customs_release_date=None,
        task_id=1,
        berthing_time='2021/08/21 06:00',
    )

    assert results[1] == ContainerItem(
        container_key='YMLU8538167',
        container_no='YMLU8538167',
        last_free_day=None,
        task_id=1,
        terminal=LocationItem(name='Y773'),
    )

    assert isinstance(results[2], RequestOption)

    assert results[3] == ExportErrorData(
        task_id=2,
        mbl_no='W236958823',
        status=CARRIER_RESULT_STATUS_ERROR,
        detail='Data was not found',
    )

    assert results[4] == MblItem(
        mbl_no='W240280894',
        por=LocationItem(name='QINGDAO, SD (CNTAO)'),
        pol=LocationItem(name='QINGDAO, SD (CNTAO)'),
        pod=LocationItem(name='LOS ANGELES, CA (USLAX)'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA (USLAX)'),
        etd=None,
        atd='2021/08/03 14:56',
        eta='2021/08/29 18:00',
        ata=None,
        firms_code='Y258',
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status='(No entry filed)',
        customs_release_date=None,
        task_id=3,
        berthing_time='2021/08/29 22:00',
    )

    assert results[5] == ContainerItem(
        container_key='YMLU8917617',
        container_no='YMLU8917617',
        last_free_day=None,
        task_id=3,
        terminal=LocationItem(name='Y258'),
    )

    assert isinstance(results[6], RequestOption)
