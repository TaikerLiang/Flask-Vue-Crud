from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == ContainerItem(
        container_key='WHSU5121845',
        container_no='WHSU5121845',
    )

    assert isinstance(results[1], RequestOption)

    assert len(results) == 2
