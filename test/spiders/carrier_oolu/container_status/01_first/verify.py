from crawler.core_carrier.items import ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='OOLU9108987',
        container_no='OOLU9108987',
        det_free_time_exp_date='10 Nov 2019, 23:59  Local',
        last_free_day='05 Nov 2019, 23:59  Local',
    )

    assert results[1] == ContainerStatusItem(
        container_key='OOLU9108987',
        description='Container Returned to Carrier (Destination)',
        location=LocationItem(name='ConGlobal Industries Inc., Atlanta, Fulton, Georgia, United States'),
        transport='Truck',
        local_date_time='07 Nov 2019, 08:08 EST',
    )

    assert results[4] == ContainerStatusItem(
        container_key='OOLU9108987',
        description='Container Deramped',
        location=LocationItem(name='Norfolk Southern Corp - Austell, Austell, Cobb, Georgia, United States'),
        transport='Rail',
        local_date_time='03 Nov 2019, 16:28 EST',
    )
