from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.rules import RoutingRequest


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerItem(
            container_no='HLBU1598798',
            container_key='HLBU1598798',
        )

        assert results[1] == ContainerItem(
            container_no='UACU5837527',
            container_key='UACU5837527',
        )

        assert isinstance(results[2], RoutingRequest)
        assert results[2].request.url == (
            'https://www.hapag-lloyd.com/en/online-business/tracing/tracing-by-booking.html?_a=tracing_by_booking'
        )
        assert results[2].request.meta['container_key'] == 'HLBU1598798'

        assert isinstance(results[3], RoutingRequest)
        assert results[3].request.meta['container_key'] == 'UACU5837527'
