from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='MSCU5633348',
        container_no='MSCU5633348',
    )

    assert results[1] == ContainerStatusItem(
        container_key='MSCU5633348',
        description='Gate In Full',
        local_date_time='08/12/2019',
        location=LocationItem(name='NINGBO, 33, CN'),
        vessel=None,
        voyage=None,
        est_or_actual='A',
    )

    assert results[3] == MblItem(
        mbl_no=None,
        pol=LocationItem(name=None),
        pod=LocationItem(name=None),
        etd=None,
        vessel=None,
        place_of_deliv=LocationItem(name=None),
        latest_update='11.12.2019 at 08:16 W. Europe Standard Time',
    )

