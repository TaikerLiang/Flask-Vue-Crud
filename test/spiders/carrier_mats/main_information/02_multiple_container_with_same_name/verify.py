from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name="NINGBO"),
        pol=LocationItem(name="NINGBO"),
        pod=LocationItem(name="LONG BEACH"),
        place_of_deliv=LocationItem(name=""),
        eta=None,
    )

    assert results[1] == ContainerItem(
        container_key="MATU2310910",
        container_no="MATU2310910",
    )

    assert isinstance(results[2], RequestOption)
