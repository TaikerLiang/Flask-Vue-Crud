from typing import List

from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results: List):
    assert results[0] == ContainerStatusItem(
        container_key='YMLU3555177',
        description='Empty Returned',
        local_date_time='2019/08/28 10:46',
        location=LocationItem(name='DALLAS (Equipment Storage Service Inc. (ESS))'),
        transport=None,
    )

    assert results[2] == ContainerStatusItem(
        container_key='YMLU3555177',
        description='Notification',
        local_date_time='2019/08/27 01:25',
        location=LocationItem(name='DALLAS, TX (Dallas Intermodal Terminal (DIT))'),
        transport='Rail',
    )

    assert results[32] == ContainerStatusItem(
        container_key='YMLU3555177',
        description='Empty to CFS',
        local_date_time='2019/07/31 19:10',
        location=LocationItem(name='KAOHSIUNG (KAOHSIUNG TERMINAL NO.3-#70)'),
        transport=None,
    )

