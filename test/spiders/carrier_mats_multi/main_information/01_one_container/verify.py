from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == MblItem(
        por=LocationItem(name="SHANGHAI"),
        pol=LocationItem(name="SHANGHAI"),
        pod=LocationItem(name="OAKLAND OICT"),
        place_of_deliv=LocationItem(name="OAKLAND"),
        eta="01/27/22",
        task_id="1",
    )

    assert results[1] == ContainerItem(
        container_key="MATU2345624",
        container_no="MATU2345624",
        task_id="1",
    )

    assert isinstance(results[2], RequestOption)
