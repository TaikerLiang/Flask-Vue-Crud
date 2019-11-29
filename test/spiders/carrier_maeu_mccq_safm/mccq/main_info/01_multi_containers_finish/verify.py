from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='589898475',
        pol=LocationItem(name='Beilun container terminal, Phase 2 -- Ningbo (Zhejiang, CN)'),
        final_dest=LocationItem(name='VIP Greenport Joint Stock Company -- Haiphong (Hai Phong, VN)'),
    )

    assert results[1] == ContainerItem(
        container_key='PONU1767353',
        container_no='PONU1767353',
        final_dest_eta='2019-10-31T04:34:00.000',
    )

    assert results[2] == ContainerStatusItem(
        container_key='PONU1767353',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-10-06T14:09:00.000',
        location=LocationItem(name='NIngbo Beilun Donghwa Cont. Transp. -- Ningbo (Zhejiang, CN)'),
        vessel='MAERSK ATLANTIC 3MY',
        voyage='941E',
        est_or_actual='A',
    )

    assert results[8] == ContainerStatusItem(
        container_key='PONU1767353',
        description='GATE-OUT',
        local_date_time='2019-11-08T00:56:00.000',
        location=LocationItem(name='VIP Greenport Joint Stock Company -- Haiphong (Hai Phong, VN)'),
        vessel='OREA M38',
        voyage='943N',
        est_or_actual='A',
    )

    assert results[9] == ContainerItem(
        container_key='PONU1947308',
        container_no='PONU1947308',
        final_dest_eta='2019-10-31T04:37:00.000',
    )

    assert results[10] == ContainerStatusItem(
        container_key='PONU1947308',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-10-05T20:39:00.000',
        location=LocationItem(name='NIngbo Beilun Donghwa Cont. Transp. -- Ningbo (Zhejiang, CN)'),
        vessel='MAERSK ATLANTIC 3MY',
        voyage='941E',
        est_or_actual='A',
    )

    assert results[16] == ContainerStatusItem(
        container_key='PONU1947308',
        description='GATE-OUT',
        local_date_time='2019-11-08T04:19:00.000',
        location=LocationItem(name='VIP Greenport Joint Stock Company -- Haiphong (Hai Phong, VN)'),
        vessel='OREA M38',
        voyage='943N',
        est_or_actual='A',
    )

