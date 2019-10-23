from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='SMCU1098525',
        description='Empty Container Release to Shipper',
        local_date_time='2019-09-25 18:00',
        location=LocationItem(name='QINGDAO,CHINA ,CHINA'),
        est_or_actual='A',
    )

    assert results[9] == ContainerStatusItem(
        container_key='SMCU1098525',
        description="'SM SHANGHAI 1907E' Arrival at Port of Discharging",
        local_date_time='2019-10-18 14:30',
        location=LocationItem(name='LONG BEACH,CA ,UNITED STATES'),
        est_or_actual='E',
    )

    assert results[13] == ContainerStatusItem(
        container_key='SMCU1098525',
        description='Empty Container Returned from Customer',
        local_date_time='2019-10-22 17:00',
        location=LocationItem(name='LONG BEACH,CA ,UNITED STATES'),
        est_or_actual='E',
    )

