from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import VoyageSpec, MblSearchResultRoutingRule


def verify(results, queue):
    assert results[0] == MblItem(
        por=LocationItem(name='Ningbo  CNNGB'),
        final_dest=LocationItem(name='Long Beach USLGB'),
        carrier_release_date=None,
        customs_release_date='24-Apr-2020',
    )

    assert results[1] == ContainerItem(
        container_key='SUDU4940770',
        container_no='SUDU4940770',
    )

    assert results[2] == ContainerStatusItem(
        container_key='SUDU4940770',
        description='Empty out for booking',
        local_date_time='06-Mar-2020 09:16',
        location=LocationItem(name='Ningbo  CNNGB'),
        vessel=None,
        voyage=None,
    )

    assert results[11] == ContainerStatusItem(
        container_key='SUDU4940770',
        description='Empty container returned',
        local_date_time='07-Apr-2020 07:08',
        location=LocationItem(name='Los Angeles USLAX'),
        vessel=None,
        voyage=None,
    )

    assert isinstance(results[12], RequestOption)
    assert results[12].rule_name == MblSearchResultRoutingRule.name

    assert queue.qsize() == 2
