from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name='NINGBO'),
        pol=LocationItem(name='NINGBO'),
        pod=LocationItem(name='LONG BEACH'),
        place_of_deliv=LocationItem(name='LONG BEACH'),
        task_id='1',
    )

    assert results[1] == ContainerItem(
        container_key='MATU2310910',
        container_no='MATU2310910',
        task_id='1',
    )

    assert isinstance(results[2], RequestOption)