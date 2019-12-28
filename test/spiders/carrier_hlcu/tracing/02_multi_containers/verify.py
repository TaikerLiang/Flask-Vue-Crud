from scrapy import Request

from crawler.core_carrier.items import ContainerItem


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

        assert isinstance(results[2], Request)
        assert results[2].meta['container_key'] == 'HLBU1598798'

        assert isinstance(results[3], Request)
        assert results[3].meta['container_key'] == 'UACU5837527'
