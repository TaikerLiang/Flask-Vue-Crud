from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    @staticmethod
    def verify(results):

        assert results[0] == ContainerStatusItem(
            container_key='HLBU2060615',
            description='Gate out empty (Truck)',
            local_date_time='2019-07-29 04:30',
            location=LocationItem(name='SHANGHAI'),
            transport='Truck',
            voyage=None,
            est_or_actual='A',
        )

        assert results[5] == ContainerStatusItem(
            container_key='HLBU2060615',
            description='Discharged (NORTHERN JUSTICE)',
            local_date_time='2019-08-19 06:26',
            location=LocationItem(name='VANCOUVER, BC'),
            transport='NORTHERN JUSTICE',
            voyage='008E',
            est_or_actual='A',
        )
