from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    @staticmethod
    def verify(results):
        assert results[0] == ContainerStatusItem(
            container_key='PCIU0142052',
            description='O/B Empty Container Released',
            local_date_time='2019-10-22 11:01:00',
            location=LocationItem(name='NINGBO'),
            transport='/',
            est_or_actual='A',
        )

        assert results[1] == ContainerStatusItem(
            container_key='PCIU0142052',
            description='Truck Gate In to O/B Terminal',
            local_date_time='2019-10-23 07:32:00',
            location=LocationItem(name='NINGBO'),
            transport='/',
            est_or_actual='A',
        )

        assert results[2] == ContainerStatusItem(
            container_key='PCIU0142052',
            description='Vessel Loading',
            local_date_time='2019-10-25 15:59:00',
            location=LocationItem(name='NINGBO'),
            transport='KOTA CEMPAKA / KCPK0043W',
            est_or_actual='A',
        )

        assert results[3] == ContainerStatusItem(
            container_key='PCIU0142052',
            description='Vessel Discharge',
            local_date_time='2019-11-18 05:00:00',
            location=LocationItem(name='JEDDAH'),
            transport='KOTA CEMPAKA / KCPK0043W',
            est_or_actual='E',
        )

        # event ignored (pending) --- Truck Gate Out from I/B Terminal
        # event ignored (pending) --- I/B Empty Container Returned

        assert len(results) == 4
