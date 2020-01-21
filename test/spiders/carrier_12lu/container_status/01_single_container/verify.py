from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(mbl_no='NOSNB9GX16042')

    assert results[1] == ContainerItem(
        container_key='SEGU3474023',
        container_no='SEGU3474023',
    )

    assert results[2] == ContainerStatusItem(
        container_key='SEGU3474023',
        description='客户提空箱',
        local_date_time='2019-12-17 23:01',
        location=LocationItem(name='宁波港'),
        vessel='NEW MINGZHOU 60',
        voyage='9085S',
    )

    assert results[5] == ContainerItem(
        container_key='SEGU3474023',
        container_no='SEGU3474023',
    )

    assert results[6] == ContainerStatusItem(
        container_key='SEGU3474023',
        description='出口装船',
        local_date_time='2019-12-20 23:18',
        location=LocationItem(name='宁波港'),
        vessel='新明州60',
        voyage='9085S',
    )

    assert results[9] == ContainerItem(
        container_key='SEGU3474023',
        container_no='SEGU3474023',
    )

    assert results[10] == ContainerStatusItem(
        container_key='SEGU3474023',
        description='进口重箱出场',
        local_date_time='2019-12-31 10:58',
        location=LocationItem(name='高雄'),
        vessel='NEW MINGZHOU 60',
        voyage='9085S',
    )
