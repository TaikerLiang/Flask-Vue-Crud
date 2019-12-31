from crawler.core_carrier.items import LocationItem, ContainerItem, ContainerStatusItem


def verify(results):

    assert results[0] == ContainerItem(
        container_key='DFSU6717570',
        container_no='DFSU6717570',
        last_free_day='Gated-out',
        mt_location=LocationItem(name='APM TERMINALS (LOS ANGELES, CA)'),
        det_free_time_exp_date='30-Jul-2019',
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
    )

    assert results[1] == ContainerStatusItem(
        container_key='DFSU6717570',
        description='Empty returned',
        local_date_time='24-Jul-2019 4:08 PM',
        location=LocationItem(name=None),
        transport=None,
    )

    assert results[3] == ContainerStatusItem(
        container_key='DFSU6717570',
        description='Discharged',
        local_date_time='21-Jul-2019 12:23 AM',
        location=LocationItem(name='LOS ANGELES, CA'),
        transport='HYUNDAI FAITH V 082E',
    )

    assert results[7] == ContainerStatusItem(
        container_key='DFSU6717570',
        description='Gate In loading port',
        local_date_time='03-Jul-2019 2:01 AM',
        location=LocationItem(name='SHANGHAI,CHINA'),
        transport='Truck',
    )
