from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='712027741',
        pol=LocationItem(name='Kaohsiung () (TW)'),
        final_dest=LocationItem(name='Johannesburg (Gauteng) (ZA)'),
    )

    assert results[1] == ContainerItem(
        container_key='MRKU8035331',
        container_no='MRKU8035331',
        final_dest_eta='2019-11-21T16:00:00.000'
    )

    assert results[2] == ContainerStatusItem(
        container_key='MRKU8035331',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-10-04T14:57:00.000',
        location=LocationItem(name='Kaohsiung () (TW)'),
        vessel='MCC CEBU H5B',
        voyage='941W',
        est_or_actual='A',
    )

    assert results[10] == ContainerStatusItem(
        container_key='MRKU8035331',
        description='GATE-OUT',
        local_date_time='2019-11-21T16:00:00.000',
        location=LocationItem(name='Johannesburg (Gauteng) (ZA)'),
        vessel=None,
        voyage=None,
        est_or_actual='E',
    )

