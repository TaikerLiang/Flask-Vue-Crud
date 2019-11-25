from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='SEGU3105940',
        container_no='SEGU3105940',
    )

    assert results[1] == ContainerStatusItem(
        container_key='SEGU3105940',
        description='Estimated Time of Arrival',
        local_date_time='10/12/2019',
        location=LocationItem(name='LOS ANGELES, CA, US'),
        vessel='MSC VEGA',
        voyage=None,
        est_or_actual='E',
    )

    assert results[5] == MblItem(
        mbl_no='MEDUH3870076',
        pol=LocationItem(name='YANTIAN, CN'),
        pod=LocationItem(name='LOS ANGELES, US'),
        etd='25/11/2019',
        vessel='MSC VEGA',
        place_of_deliv=LocationItem(name=None),
        latest_update='25.11.2019 at 09:57 W. Europe Standard Time',
    )

