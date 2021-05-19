from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:
    def verify(self, results):
        assert results[0] == ContainerStatusItem(
            container_key='EITU1673822',
            description='Empty pick-up by merchant haulage',
            local_date_time='SEP-04-2019',
            location=LocationItem(name='TAICHUNG (TW)'),
        )

        assert results[10] == ContainerStatusItem(
            container_key='EITU1673822',
            description='Pick-up by merchant haulage',
            local_date_time='OCT-14-2019',
            location=LocationItem(name='HOUSTON, TX (US)'),
        )
