from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name='HAIPHONG (VN)'),
        pod=LocationItem(name='LONG BEACH, CA (US)'),
        final_dest=LocationItem(name=None),
        eta='Sun 08 Sep 2019 15:00',
        ata=None,
    )

    assert results[1] == ContainerItem(
        container_key='TGCU0067220',
        container_no='TGCU0067220',
    )

    assert results[2] == ContainerStatusItem(
        container_key='TGCU0067220',
        local_date_time='Thu 08 Aug 2019 21:25',
        description='Empty in depot',
        location=LocationItem(name='HAIPHONG'),
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='TGCU0067220',
        local_date_time='Mon 19 Aug 2019 11:04',
        description='Discharged in transhipment',
        location=LocationItem(name='NANSHA'),
        est_or_actual='A'
    )

    assert results[8] == ContainerStatusItem(
        container_key='TGCU0067220',
        local_date_time='Sun 08 Sep 2019 15:00',
        description='Arrival final port of discharge',
        location=LocationItem(name='LONG BEACH, CA'),
        est_or_actual='E'
    )
