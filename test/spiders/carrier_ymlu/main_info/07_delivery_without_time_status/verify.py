from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W209139591',
        por=LocationItem(name='KAOHSIUNG, Taiwan'),
        pol=LocationItem(name='KAOHSIUNG, Taiwan'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='EL PASO, TX, USA'),
        etd=None,
        atd='2020/05/26 10:10',
        eta=None,
        ata='2020/06/10 03:42',
        firms_code='Y773',
        carrier_status='Steamship Release',
        carrier_release_date='2020/06/02 17:49',
        customs_release_status='(not yet Customs Release)',
        customs_release_date=None,
    )

    assert results[1] == ContainerItem(
        container_key='TGHU5294991',
        container_no='TGHU5294991',
        last_free_day=None,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=TGHU5294991&blno=W209139591&movertype=11&lifecycle=1'
    )
