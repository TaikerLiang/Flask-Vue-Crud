from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name=None),
            pol=LocationItem(name='NINGBO (CN)'),
            pod=LocationItem(name='SAVANNAH, GA (US)'),
            final_dest=LocationItem(name='ATLANTA, GA (US)'),
            eta='Thu 05 Sep 2019 06:00',
            ata=None,
        )

        assert results[1] == ContainerItem(
            container_no='CMAU4349470',
        )

        assert results[2] == ContainerStatusItem(
            container_no='CMAU4349470',
            timestamp='Thu 18 Jul 2019 22:00',
            description='Empty to shipper',
            location=LocationItem(name='NINGBO'),
            est_or_actual='A',
        )

        assert results[7] == ContainerStatusItem(
            container_no='CMAU4349470',
            timestamp='Thu 05 Sep 2019 06:00',
            description='Arrival final port of discharge',
            location=LocationItem(name='SAVANNAH'),
            est_or_actual='E'
        )
