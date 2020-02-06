from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results):
    assert results[0] == MblItem(mbl_no='NOSNB9TZ35829')

    assert results[1] == ContainerItem(
        container_key='NBYU4000103',
        container_no='NBYU4000103',
    )

    assert results[2] == ContainerStatusItem(
        container_key='NBYU4000103',
        description='进口重箱出场',
        local_date_time='2019-10-24 13:20',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[3] == ContainerItem(
        container_key='NBYU4005701',
        container_no='NBYU4005701',
    )

    assert results[4] == ContainerStatusItem(
        container_key='NBYU4005701',
        description='进口重箱出场',
        local_date_time='2019-10-28 16:14',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[5] == ContainerItem(
        container_key='NBYU4006673',
        container_no='NBYU4006673',
    )

    assert results[6] == ContainerStatusItem(
        container_key='NBYU4006673',
        description='进口重箱出场',
        local_date_time='2019-10-25 12:23',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[7] == ContainerItem(
        container_key='NBYU5000849',
        container_no='NBYU5000849',
    )

    assert results[8] == ContainerStatusItem(
        container_key='NBYU5000849',
        description='进口重箱出场',
        local_date_time='2019-10-24 08:24',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[15] == ContainerItem(
        container_key='NBYU5000303',
        container_no='NBYU5000303',
    )

    assert results[16] == ContainerStatusItem(
        container_key='NBYU5000303',
        description='出口装船',
        local_date_time='2019-10-18 13:07',
        location=LocationItem(name='宁波港'),
        vessel='新明州60',
        voyage='9067S',
    )

    assert isinstance(results[41], RoutingRequest)
