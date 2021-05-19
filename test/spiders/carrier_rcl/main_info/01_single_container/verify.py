from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='NGBCB19030998',
        pol=LocationItem(name='Ningbo Beilun International Container Terminals Limited, Ningbo , ' 'China'),
        pod=LocationItem(name='Tips Co., Ltd. (B4), Laem Chabang , Thailand'),
        etd='01 Nov 2019',
        eta='09 Nov 2019',
    )

    assert results[1] == ContainerItem(
        container_key='CAXU6726226',
        container_no='CAXU6726226',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CAXU6726226',
        local_date_time='2019-Oct-29 08:09',
        description='Out Depot',
        location=LocationItem(name='China, Ningbo'),
    )

    assert results[9] == ContainerStatusItem(
        container_key='CAXU6726226',
        local_date_time='2019-Nov-15 16:24',
        description='In Depot',
        location=LocationItem(name='Thailand, Laem Chabang : 99 Container Depot'),
    )
