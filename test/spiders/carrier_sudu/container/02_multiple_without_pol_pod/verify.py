from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import MblSearchResultRoutingRule


def verify(results, queue):
    assert results[0] == MblItem(
        por=LocationItem(name='Guatemala City GTGUA'),
        final_dest=LocationItem(name='West Columbia USWCB'),
        carrier_release_date='18-Mar-2020',
        customs_release_date='17-Mar-2020',
    )

    assert results[1] == ContainerItem(
        container_key='HASU4838894',
        container_no='HASU4838894',
    )

    assert results[2] == ContainerStatusItem(
        container_key='HASU4838894',
        description='Empty out for booking',
        local_date_time='04-Mar-2020 10:06',
        location=LocationItem(name='Guatemala City GTGUA'),
        vessel=None,
        voyage=None,
    )

    assert results[10] == ContainerStatusItem(
        container_key='HASU4838894',
        description='Empty container returned',
        local_date_time='25-Mar-2020 14:00',
        location=LocationItem(name='Savannah USSAV'),
        vessel=None,
        voyage=None,
    )

    assert isinstance(results[11], RequestOption)
    assert results[11].rule_name == MblSearchResultRoutingRule.name

    assert queue.qsize() == 0
