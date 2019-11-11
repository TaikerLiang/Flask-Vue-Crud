from crawler.core_carrier.items import MblItem, VesselItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='GLDU7632978',
        container_no='GLDU7632978',
    )

    assert results[1] == ContainerStatusItem(
        container_key='GLDU7632978',
        description='Empty in Container Yard',
        local_date_time='10/10/2019',
        location=LocationItem(name='LOS ANGELES, CA, US'),
        vessel=None,
        voyage=None,
        est_or_actual='A',
    )

    assert results[10] == ContainerStatusItem(
        container_key='GLDU7632978',
        description='Empty to Shipper',
        local_date_time='04/09/2019',
        location=LocationItem(name='ZHAPU, 33, CN'),
        vessel=None,
        voyage=None,
        est_or_actual='A',
    )

    assert results[11] == MblItem(
        mbl_no='MEDUN4194175',
        pol='NINGBO, CN',
        pod='LONG BEACH, US',
        etd='18/09/2019',
        vessel='MSC BERYL',
        place_of_deliv='LONG BEACH, US',
        latest_update='05.11.2019 at 10:50 W. Europe Standard Time',
    )

