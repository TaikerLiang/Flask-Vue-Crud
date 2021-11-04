from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    @staticmethod
    def verify(results):

        assert results[0] == ContainerStatusItem(
            container_key='UACU5837527',
            description='Gate out empty (Truck)',
            local_date_time='2019-11-21 22:37',
            location=LocationItem(name='SHANGHAI'),
            transport='Truck',
            voyage=None,
            est_or_actual='A',
        )

        assert results[4] == ContainerStatusItem(
            container_key='UACU5837527',
            description='Vessel arrival (MOL MATRIX)',
            local_date_time='2019-12-14 07:00',
            location=LocationItem(name='LOS ANGELES, CA'),
            transport='MOL MATRIX',
            voyage='054E',
            est_or_actual='E',
        )
