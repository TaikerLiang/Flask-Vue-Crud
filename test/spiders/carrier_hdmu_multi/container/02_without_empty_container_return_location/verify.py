from crawler.core_carrier.items import LocationItem, ContainerItem, ContainerStatusItem, MblItem


def verify(results):
    assert results[0] == MblItem(task_id='1')

    assert results[1] == ContainerItem(
        container_key='TRLU5950868',
        container_no='TRLU5950868',
        last_free_day=None,
        mt_location=LocationItem(name=None),
        det_free_time_exp_date=None,
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
        task_id='1',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TRLU5950868',
        description='Discharged',
        local_date_time='03-Jan-2020 5:26 PM',
        location=LocationItem(name='DAMMAM, SAUDI ARABIA'),
        transport='HYUNDAI BRAVE V 082W',
        task_id='1',
    )

    assert results[6] == ContainerStatusItem(
        container_key='TRLU5950868',
        description='Gate In loading port',
        local_date_time='12-Dec-2019 8:13 PM',
        location=LocationItem(name='NINGBO, CHINA'),
        transport='Truck',
        task_id='1',
    )

    assert results[7] == ContainerStatusItem(
        container_key='TRLU5950868',
        description='Released to the shipper for stuffing',
        local_date_time='12-Dec-2019 4:29 PM',
        location=LocationItem(name='NINGBO, CHINA'),
        transport='Truck',
        task_id='1',
    )