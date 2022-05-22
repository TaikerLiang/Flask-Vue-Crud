from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no="W209047989",
        por=LocationItem(name="KAOHSIUNG, Taiwan"),
        pol=LocationItem(name="KAOHSIUNG, Taiwan"),
        pod=LocationItem(name="LOS ANGELES, CA, USA"),
        place_of_deliv=LocationItem(name="CHINO, CA, USA"),
        etd="2010/06/15 07:30",
        atd=None,
        eta=None,
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        berthing_time=None,
        vessel=None,
        voyage="2010_PSW023E",
    )

    assert results[1] == ContainerItem(
        container_key="WWWU9601440",
        container_no="WWWU9601440",
        last_free_day=None,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        "https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?"
        "rdolType=BL&ctnrno=WWWU9601440&blno=W209047989&movertype=11&lifecycle="
    )
