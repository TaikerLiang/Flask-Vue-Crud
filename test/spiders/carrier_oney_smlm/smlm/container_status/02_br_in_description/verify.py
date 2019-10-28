from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[7] == ContainerStatusItem(
        container_key='SDCU6132558',
        description='Gate Out from Inbound Terminal OR Shuttled to ODCY',
        local_date_time='2019-11-01 23:00',
        location=LocationItem(name='LONG BEACH,CA ,UNITED STATES'),
        est_or_actual='E',
    )

