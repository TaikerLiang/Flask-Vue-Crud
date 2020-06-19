from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerItem(
            container_no='HLBU2060615',
            container_key='HLBU2060615',
        )

        assert isinstance(results[1], RequestOption)
        assert results[1].url == (
            'https://www.hapag-lloyd.com/en/online-business/tracing/tracing-by-booking.html?_a=tracing_by_booking'
        )
        assert results[1].meta['container_key'] == 'HLBU2060615'
