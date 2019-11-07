from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerStatusItem(
            container_key='PCIU9477648',
            description='O/B Empty Container Released',
            local_date_time='2019-06-18 18:00:00',
            location=LocationItem(name='NANJING'),
            transport='/',
        )
        assert results[1] == ContainerStatusItem(
            container_key='PCIU9477648',
            description='Truck Gate In to O/B Terminal',
            local_date_time='2019-06-20 01:54:00',
            location=LocationItem(name='NANJING'),
            transport='/',
        )
