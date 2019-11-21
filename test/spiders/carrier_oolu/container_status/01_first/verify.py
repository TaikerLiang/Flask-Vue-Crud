from crawler.core_carrier.items import ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='OOLU910898',
        container_no='OOLU910898',
        det_free_time_exp_date='10 Nov 2019, 23:59  Local',
        last_free_day='05 Nov 2019, 23:59  Local',
    )

    assert results[1] == ContainerStatusItem(
        container_key='OOLU910898',
        description='Container Returned to Carrier',
        location=LocationItem(name='ConGlobal Industries Inc., Atlanta, Fulton, Georgia, United States'),
        transport='Truck',
        local_date_time='07 Nov 2019, 08:08 EST',
    )
