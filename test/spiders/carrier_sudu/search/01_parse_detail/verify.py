from typing import List

from scrapy import Request

from crawler.core_carrier.items import ContainerStatusItem, MblItem, LocationItem, ContainerItem


def verify(results: List):
    assert results[0] == MblItem(
        por=LocationItem(name='Shanghai CNSHA'),
        final_dest=LocationItem(name='Houston USHOU'),
        carrier_release_date=None,
        customs_release_date='22-Oct-2019'
    )

    assert results[1] == ContainerItem(
        container_key='MSKU1906021',
        container_no='MSKU1906021',
    )

    assert results[2] == ContainerStatusItem(
        container_key='MSKU1906021',
        description='Empty out for booking',
        local_date_time='19-Sep-2019 22:31',
        location=LocationItem(name='Shanghai CNSHA'),
        vessel=None,
        voyage=None,
    )

    assert results[9] == ContainerStatusItem(
        container_key='MSKU1906021',
        description='Discharged from vessel',
        local_date_time='24-Oct-2019 13:16',
        location=LocationItem(name='Houston USHOU'),
        vessel='MSC BARBARA',
        voyage='939E',
    )

    assert isinstance(results[12], Request)
    assert results[12].meta == {
        'CARRIER_CORE_RULE_NAME': 'VOYAGE',
        'voyage_location': 'Shanghai CNSHA',
        'voyage_direction': 'Departure',
    }

    assert isinstance(results[13], Request)
    assert results[13].meta == {
        'CARRIER_CORE_RULE_NAME': 'VOYAGE',
        'voyage_location': 'Houston USHOU',
        'voyage_direction': 'Arrival',
    }
