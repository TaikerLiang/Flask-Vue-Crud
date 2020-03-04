from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='FSCU4872850',
        container_no='FSCU4872850',
    )

    assert results[1] == ContainerStatusItem(
        container_key='FSCU4872850',
        description='Estimated Time of Arrival',
        local_date_time='24/03/2020',
        location=LocationItem(name='GIOIA TAURO, IT'),
        vessel='MSC JADE',
        voyage=None,
        est_or_actual='E',
    )

    assert results[4] == ContainerStatusItem(
        container_key='FSCU4872850',
        description='Empty to Shipper',
        local_date_time='19/02/2020',
        location=LocationItem(name='NINGBO, 33, CN'),
        vessel=None,
        voyage=None,
        est_or_actual='A',
    )

    assert results[10] == MblItem(
        mbl_no='MEDUNG283959',
        pol=LocationItem(name='NINGBO, CN'),
        pod=LocationItem(name='SUAPE, BR'),
        etd='26/02/2020',
        vessel='MSC JADE',
        place_of_deliv=LocationItem(name='SUAPE, BR'),
        latest_update='04.03.2020 at 04:18 W. Europe Standard Time',
    )

