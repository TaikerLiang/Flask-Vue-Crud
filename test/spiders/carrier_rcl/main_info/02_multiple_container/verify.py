from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='NGBCB19030160',
        pol=LocationItem(name='Ningbo Beilun International Container Terminals Limited, Ningbo , '
         'China'),
        pod=LocationItem(name='The Port Authority Of Thailand.   (Pat), Bangkok , Thailand'),
        etd='26 Oct 2019',
        eta='04 Nov 2019',
    )

    assert results[1] == ContainerItem(
        container_key='CAIU4414530',
        container_no='CAIU4414530',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CAIU4414530',
        local_date_time='2019-Oct-22 08:02',
        description='Out Depot',
        location=LocationItem(name='China, Ningbo'),
    )

    assert results[7] == ContainerStatusItem(
        container_key='CAIU4414530',
        local_date_time='2019-Nov-09 09:26',
        description='In Depot',
        location=LocationItem(name='Thailand, Bangkok : 127 Depot'),
    )

    assert results[8] == ContainerItem(
        container_key='REGU5099614',
        container_no='REGU5099614',
    )

    assert results[9] == ContainerStatusItem(
        container_key='REGU5099614',
        local_date_time='2019-Oct-22 06:01',
        description='Out Depot',
        location=LocationItem(name='China, Ningbo'),
    )

    assert results[14] == ContainerStatusItem(
        container_key='REGU5099614',
        local_date_time='2019-Nov-09 09:15',
        description='In Depot',
        location=LocationItem(name='Thailand, Bangkok : 127 Depot'),
    )
