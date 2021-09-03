from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='I209365239',
        por=LocationItem(name='KAOHSIUNG, Taiwan'),
        pol=LocationItem(name='KAOHSIUNG, Taiwan'),
        pod=LocationItem(name='MANILA (NORTH HARBOUR), Philippines'),
        place_of_deliv=LocationItem(name='MANILA (NORTH HARBOUR), Philippines'),
        etd=None,
        atd='2019/10/01 10:35',
        eta=None,
        ata='2019/10/04 15:00',
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='TGHU5309509',
        container_no='TGHU5309509',
        last_free_day=None,
        task_id=1,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/'
        'ctconnect.aspx?rdolType=BL&ctnrno=TGHU5309509&blno=I209365239&movertype=11&lifecycle=2'
    )
