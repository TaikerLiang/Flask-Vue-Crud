from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='MEDUH3870035',
        pol=LocationItem(name='YANTIAN, CN'),
        pod=LocationItem(name='LOS ANGELES, US'),
        etd='09/12/2019',
        vessel='MAERSK ENSHI',
        place_of_deliv=LocationItem(name=None),
        latest_update='09.12.2019 at 06:56 W. Europe Standard Time',
    )

