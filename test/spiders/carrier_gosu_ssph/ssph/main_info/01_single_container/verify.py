from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHJOR8017471',
        por=LocationItem(name=None),
        pol=LocationItem(name="Tanjung Pelepas, Malaysia"),
        pod=LocationItem(name="Savannah , U.S.A."),
        final_dest=LocationItem(name='Atlanta , U.S.A.'),
    )

    assert results[1] == VesselItem(
        vessel_key='Maersk Semakau',
        vessel='Maersk Semakau',
        voyage='8',
        etd='23-Nov-2019',
        eta='26-Dec-2019',
        pol=LocationItem(name='Tanjung Pelepas, Malaysia (POL)'),
        pod=LocationItem(name='Savannah (GA), U.S.A. (POD)'),
    )

    assert results[2] == ContainerItem(
        container_key='ZCSU8832075',
        container_no='ZCSU8832075',
    )

    assert isinstance(results[3], RequestOption)
