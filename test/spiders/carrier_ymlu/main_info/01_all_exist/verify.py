from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W216104890',
        por=LocationItem(name='TAICHUNG, Taiwan'),
        pol=LocationItem(name='KAOHSIUNG, Taiwan'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA, USA'),
        etd=None,
        atd='2020/03/10 07:58',
        eta=None,
        ata='2020/03/24 03:42',
        firms_code='Y773',
        carrier_status='Steamship Release',
        carrier_release_date='2020/03/17 16:17',
        customs_release_status='Customs Release',
        customs_release_date='2020/03/23 14:25',
        berthing_time='2020/03/24 05:00',
    )

    assert results[1] == ContainerItem(
        container_key='BMOU6194498',
        container_no='BMOU6194498',
        last_free_day=None,
        terminal=LocationItem(name='Y773'),
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?'
        'rdolType=BL&ctnrno=BMOU6194498&blno=W216104890&movertype=11&lifecycle=1'
    )
