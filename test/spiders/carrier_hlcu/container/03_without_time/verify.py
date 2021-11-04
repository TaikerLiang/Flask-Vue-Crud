from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    @staticmethod
    def verify(results):

        assert results[4] == ContainerStatusItem(
            container_key='TCLU7285161',
            description='Departure from (Combined Waterway)',
            local_date_time='2020-01-09 00:00',
            location=LocationItem(name='TOKYO'),
            transport='Combined Waterway',
            voyage=None,
            est_or_actual='E',
        )
