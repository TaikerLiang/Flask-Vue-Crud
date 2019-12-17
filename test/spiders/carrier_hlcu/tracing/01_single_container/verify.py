from scrapy import Request

from crawler.core_carrier.items import ContainerItem


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerItem(
            container_no='HLBU2060615',
            container_key='HLBU2060615',
        )

        assert isinstance(results[1], Request)
        assert results[1].meta['container_key'] == 'HLBU2060615'
