from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        pod=LocationItem(
            name='TOWNSVILLE',
            un_lo_code='AUTSV',
        ),
        pol=LocationItem(
            name='KAOHSIUNG',
            un_lo_code='TWKHH',
        ),
        eta='2019-10-28 00:00:00',
        vessel='KOTA NAGA',
        voyage='162N',
    )

    assert results[1] == MblItem(
        mbl_no='KHH19028854',
    )

    assert results[2] == ContainerItem(
        container_key='PCIU7979631',
        container_no='PCIU7979631',
    )

    assert results[3] == ContainerStatusItem(
        container_key='PCIU7979631',
        local_date_time='2019-10-29 10:36:00',
        location=LocationItem(name='TOWNSVILLE (Townsville Hubert Street Depot)'),
        description='GATE IN TRUCKING',
    )

    assert results[10] == ContainerStatusItem(
        container_key='PCIU7979631',
        local_date_time='2019-09-17 13:15:00',
        location=LocationItem(name='KAOHSIUNG (HMM KAOHSIUNG CNTR TERMINAL)'),
        description='GATE IN FULL',
    )

    assert results[11] == MblItem(
        mbl_no='KHH19028854',
    )

    assert results[12] == ContainerItem(
        container_key='PCIU7988443',
        container_no='PCIU7988443',
    )

    assert results[13] == ContainerStatusItem(
        container_key='PCIU7988443',
        local_date_time='2019-10-29 10:32:00',
        location=LocationItem(name='TOWNSVILLE (Townsville Hubert Street Depot)'),
        description='GATE IN TRUCKING',
    )

    assert results[20] == ContainerStatusItem(
        container_key='PCIU7988443',
        local_date_time='2019-09-17 11:30:00',
        location=LocationItem(name='KAOHSIUNG (HMM KAOHSIUNG CNTR TERMINAL)'),
        description='GATE IN FULL',
    )
