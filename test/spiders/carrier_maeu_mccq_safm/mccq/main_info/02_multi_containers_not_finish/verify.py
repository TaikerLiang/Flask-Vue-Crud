from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='588455529',
        por=LocationItem(name='Ningbo-Zhoushan Yongzhou Terminal -- Ningbo (Zhejiang, CN)'),
        final_dest=LocationItem(name='Hanjin Busan New Port Co. Ltd -- Busan (KR)'),
    )

    assert results[1] == ContainerItem(
        container_key='PONU0051805',
        container_no='PONU0051805',
        final_dest_eta='2019-11-28T21:00:00.000',
    )

    assert results[2] == ContainerStatusItem(
        container_key='PONU0051805',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-11-20T06:43:00.000',
        location=LocationItem(name='Ningbo Hongda Cont Storage & Trans -- Ningbo (Zhejiang, CN)'),
        vessel='ALDI WAVE I7F',
        voyage='947E',
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='PONU0051805',
        description='GATE-OUT',
        local_date_time='2019-11-28T21:00:00.000',
        location=LocationItem(name='Hanjin Busan New Port Co. Ltd -- Busan (KR)'),
        vessel='ALDI WAVE I7F',
        voyage='947E',
        est_or_actual='E',
    )

    assert results[7] == ContainerItem(
        container_key='TCKU3481960',
        container_no='TCKU3481960',
        final_dest_eta='2019-11-28T21:00:00.000',
    )

    assert results[8] == ContainerStatusItem(
        container_key='TCKU3481960',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-11-20T06:43:00.000',
        location=LocationItem(name='Ningbo Hongda Cont Storage & Trans -- Ningbo (Zhejiang, CN)'),
        vessel='ALDI WAVE I7F',
        voyage='947E',
        est_or_actual='A',
    )

    assert results[12] == ContainerStatusItem(
        container_key='TCKU3481960',
        description='GATE-OUT',
        local_date_time='2019-11-28T21:00:00.000',
        location=LocationItem(name='Hanjin Busan New Port Co. Ltd -- Busan (KR)'),
        vessel='ALDI WAVE I7F',
        voyage='947E',
        est_or_actual='E',
    )
