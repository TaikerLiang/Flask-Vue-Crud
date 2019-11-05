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
        eta='2019-09-08 00:06:00',
        vessel='KOTA NAGA',
        voyage='161N',
    )

    assert results[1] == MblItem(
        mbl_no='KHH19028789',
    )

    assert results[2] == ContainerItem(
        container_key='PCIU7967353',
        container_no='PCIU7967353',
    )

    assert results[3] == ContainerStatusItem(
        container_key='PCIU7967353',
        local_date_time='2019-09-12 18:03:00',
        location=LocationItem(name='TOWNSVILLE (Townsville Hubert Street Depot)'),
        description='GATE IN AVAILABLE',
    )

    assert results[10] == ContainerStatusItem(
        container_key='PCIU7967353',
        local_date_time='2019-08-06 18:45:00',
        location=LocationItem(name='KAOHSIUNG (HMM KAOHSIUNG CNTR TERMINAL)'),
        description='GATE IN FULL',
    )
