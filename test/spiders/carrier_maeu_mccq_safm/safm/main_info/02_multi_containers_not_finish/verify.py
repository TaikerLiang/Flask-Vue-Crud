from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='712044685',
        pol=LocationItem(name='Kaohsiung () (TW)'),
        final_dest=LocationItem(name='Alexandria () (EG)'),
    )

    assert results[1] == ContainerItem(
        container_key='FCIU4198511',
        container_no='FCIU4198511',
        final_dest_eta='2019-12-18T14:01:00.000'
    )

    assert results[2] == ContainerStatusItem(
        container_key='FCIU4198511',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-11-08T15:26:00.000',
        location=LocationItem(name='Kaohsiung () (TW)'),
        vessel='MAERSK ARAS F1Y',
        voyage='945W',
        est_or_actual='A',
    )

    assert results[10] == ContainerStatusItem(
        container_key='FCIU4198511',
        description='GATE-OUT',
        local_date_time='2019-12-18T14:01:00.000',
        location=LocationItem(name='Alexandria () (EG)'),
        vessel='WADI ALRAYAN B22',
        voyage='949W',
        est_or_actual='E',
    )

    assert results[11] == ContainerItem(
        container_key='MRSU0260637',
        container_no='MRSU0260637',
        final_dest_eta='2019-12-18T14:01:00.000'
    )

    assert results[12] == ContainerStatusItem(
        container_key='MRSU0260637',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-11-08T16:54:00.000',
        location=LocationItem(name='Kaohsiung () (TW)'),
        vessel='MAERSK ARAS F1Y',
        voyage='945W',
        est_or_actual='A',
    )

    assert results[20] == ContainerStatusItem(
        container_key='MRSU0260637',
        description='GATE-OUT',
        local_date_time='2019-12-18T14:01:00.000',
        location=LocationItem(name='Alexandria () (EG)'),
        vessel='WADI ALRAYAN B22',
        voyage='949W',
        est_or_actual='E',
    )

