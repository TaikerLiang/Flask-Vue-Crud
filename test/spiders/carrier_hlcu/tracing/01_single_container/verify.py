
from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.rules import RoutingRequest


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerItem(
            container_no='HLBU2060615',
            container_key='HLBU2060615',
        )

        assert isinstance(results[1], RoutingRequest)
        assert results[1].request.url == (
            'https://www.hapag-lloyd.com/en/online-business/tracing/tracing-by-booking.html?_a=tracing_by_booking'
        )
        assert results[1].request.meta['container_key'] == 'HLBU2060615'
