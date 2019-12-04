from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='586118841',
        por=LocationItem(name='YanTian Intl. Container Terminal -- Yantian (Guangdong, CN)'),
        final_dest=LocationItem(name='LSA APM Terminal Pier 400( W185 ) -- Los Angeles (California, US)'),
    )

    assert results[1] == ContainerItem(
        container_key='TCKU6590749',
        container_no='TCKU6590749',
        final_dest_eta='2019-11-08T23:56:00.000'
    )

    assert results[2] == ContainerStatusItem(
        container_key='TCKU6590749',
        description='GATE-OUT-EMPTY',
        local_date_time='2019-10-16T19:12:00.000',
        location=LocationItem(name='YanTian Intl. Container Terminal -- Yantian (Guangdong, CN)'),
        vessel='MAERSK EMDEN 81A',
        voyage='942N',
        est_or_actual='A',
    )

    assert results[6] == ContainerStatusItem(
        container_key='TCKU6590749',
        description='GATE-OUT',
        local_date_time='2019-11-13T10:45:00.000',
        location=LocationItem(name='LSA APM Terminal Pier 400( W185 ) -- Los Angeles (California, US)'),
        vessel='MAERSK EMDEN 81A',
        voyage='942N',
        est_or_actual='A',
    )

