from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name=None),
            pol=LocationItem(name='NINGBO (CN)'),
            pod=LocationItem(name='LOS ANGELES, CA (US)'),
            final_dest=LocationItem(name=None),
            eta=None,
            ata='Wed 03 Jul 2019 08:38',
        )

        assert results[1] == ContainerItem(
            container_no='TRLU6600099',
        )

        assert results[2] == ContainerStatusItem(
            container_no='TRLU6600099',
            timestamp='Tue 28 May 2019 12:38',
            description='Empty in depot',
            location=LocationItem(name='NINGBO'),
            est_or_actual='A',
        )

        assert results[8] == ContainerStatusItem(
            container_no='TRLU6600099',
            timestamp='Tue 09 Jul 2019 08:21',
            description='Off hire empty',
            location=LocationItem(name='LOS ANGELES, CA'),
            est_or_actual='A'
        )
