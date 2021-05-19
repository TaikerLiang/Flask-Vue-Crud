from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='DFSU7597714',
        local_date_time='2019/10/24 14:50',
        description='LADEN CTNR LOADED ON BOARD VESSEL.(MOTHER VESSEL,FIXED SLOT CHARTER/JOINT VENTURE VESSEL)',
        location=LocationItem(name='QINGDAO QIANWAN CTNR TERMINAL CO,LTD.'),
    )

    assert results[2] == ContainerStatusItem(
        container_key='DFSU7597714',
        local_date_time='2019/10/21 22:48',
        description='INBOUND/OUTBOUND LADEN CTNR MOVE FROM ONE PIER/TERMINAL TO ANOTHER ONE BY TRUCKER/RAIL.',
        location=LocationItem(name='Qingdao Port & Win International Logistics Co., LTD'),
    )

    assert results[7] == ContainerStatusItem(
        container_key='DFSU7597714',
        local_date_time='2019/09/27 00:00',
        description='Full container(FCL) discharged from vessel OR GATE IN to Pier/Terminal',
        location=LocationItem(name='QINGDAO QIANWAN CTNR TERMINAL CO,LTD.'),
    )

    assert results[11] == ContainerStatusItem(
        container_key='DFSU7597714',
        local_date_time='2019/08/27 14:04',
        description='EMPTY CONTAINER DISCHARGED FROM VESSEL OR GATE IN TO PIER/TERMINAL/OFF-DOCK DEPOT (EMPTY AVAILABLE)',
        location=LocationItem(name='Reefco Container Services (India) Pvt Ltd'),
    )
