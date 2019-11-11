from crawler.core_carrier.items import MblItem, VesselItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='MSCU4333731',
        container_no='MSCU4333731',
    )

    assert results[1] == ContainerStatusItem(
        container_key='MSCU4333731',
        description='Estimated Time of Arrival',
        local_date_time='12/12/2019',
        location=LocationItem(name='MIAMI, FL, US'),
        vessel='MAERSK KALAMATA',
        voyage=None,
        est_or_actual='E',
    )

    assert results[6] == ContainerStatusItem(
        container_key='MSCU4333731',
        description='Empty to Shipper',
        local_date_time='23/10/2019',
        location=LocationItem(name='XIAMEN, 35, CN'),
        vessel=None,
        voyage=None,
        est_or_actual='A',
    )

    assert results[7] == MblItem(
        mbl_no='MEDUXA281435',
        pol='XIAMEN, CN',
        pod='MIAMI, US',
        etd='27/10/2019',
        vessel='GUSTAV MAERSK',
        place_of_deliv='MIAMI, US',
        latest_update='05.11.2019 at 11:32 W. Europe Standard Time',
    )

