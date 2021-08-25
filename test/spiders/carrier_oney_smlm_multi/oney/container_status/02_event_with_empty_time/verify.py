from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='FDCU0637220',
        description='Empty Container Release to Shipper',
        local_date_time='2019-10-28 21:57',
        location=LocationItem(name='HO CHI MINH ,VIETNAM'),
        est_or_actual='A',
        task_id=1,
    )

    assert results[1] == ContainerStatusItem(
        container_key='FDCU0637220',
        description='Gate In to Outbound Terminal',
        local_date_time='2019-10-29 13:58',
        location=LocationItem(name='HO CHI MINH ,VIETNAM'),
        est_or_actual='A',
        task_id=1,
    )

    # Event ignored (empty time) --- Feeder Loading at O/B Inland Port

    assert results[2] == ContainerStatusItem(
        container_key='FDCU0637220',
        description='Feeder Departure from O/B Inland Port',
        local_date_time='2019-11-04 02:57',
        location=LocationItem(name='HO CHI MINH ,VIETNAM'),
        est_or_actual='A',
        task_id=1,
    )

    assert results[3] == ContainerStatusItem(
        container_key='FDCU0637220',
        description='Outbound Feeder Arrival at Inland Port',
        local_date_time='2019-11-04 18:41',
        location=LocationItem(name='CAI MEP ,VIETNAM'),
        est_or_actual='A',
        task_id=1,
    )

    # Event ignored (empty time) --- Water POL Unloading Destination

    assert results[4] == ContainerStatusItem(
        container_key='FDCU0637220',
        description="Loaded on 'NYK ARGUS 102E' at Port of Loading",
        local_date_time='2019-11-05 10:36',
        location=LocationItem(name='CAI MEP ,VIETNAM'),
        est_or_actual='A',
        task_id=1,
    )
