from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(mbl_no='NOSNB9TZ35829')

    assert results[1] == ContainerItem(
        container_key='NBYU5000303',
        container_no='NBYU5000303',
    )

    assert results[2] == ContainerStatusItem(
        container_key='NBYU5000303',
        description='空箱入场',
        local_date_time='2019-10-29 15:16',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[3] == ContainerItem(
        container_key='NBYU4000103',
        container_no='NBYU4000103',
    )

    assert results[4] == ContainerStatusItem(
        container_key='NBYU4000103',
        description='空箱入场',
        local_date_time='2019-10-25 15:06',
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
        description='空箱入场',
        local_date_time='2019-10-25 17:56',
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
        description='空箱入场',
        local_date_time='2019-10-24 15:42',
        location=LocationItem(name='台中'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )

    assert results[9] == ContainerItem(
        container_key='NBYU4000103',
        container_no='NBYU4000103',
    )

    assert results[10] == ContainerStatusItem(
        container_key='NBYU4000103',
        description='客户提空箱',
        local_date_time='2019-10-15 13:49',
        location=LocationItem(name='宁波港'),
        vessel='NEW MINGZHOU 60',
        voyage='9067S',
    )
