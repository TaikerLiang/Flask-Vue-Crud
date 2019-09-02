from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name=None),
            pol=LocationItem(name='SHANGHAI (CN)'),
            pod=LocationItem(name='LOS ANGELES, CA (US)'),
            final_dest=LocationItem(name='HOUSTON, TX (US)'),
            eta=None,
            ata='Mon 17 Jun 2019 00:36',
        )

        assert results[1] == ContainerItem(
            container_no='TCNU1868370',
        )

        assert results[2] == ContainerStatusItem(
            container_no='TCNU1868370',
            timestamp='Wed 29 May 2019 03:06',
            description='Empty to shipper',
            location=LocationItem(name='SHANGHAI'),
            est_or_actual='A',
        )

        assert results[5] == ContainerStatusItem(
            container_no='TCNU1868370',
            timestamp='Mon 17 Jun 2019 00:36',
            description='Discharged',
            location=LocationItem(name='LOS ANGELES, CA'),
            est_or_actual='A'
        )

        assert results[11] == ContainerStatusItem(
            container_no='TCNU1868370',
            timestamp='Mon 24 Jun 2019 17:15',
            description='Train arrival for import',
            location=LocationItem(name='HOUSTON, TX'),
            est_or_actual='A'
        )
