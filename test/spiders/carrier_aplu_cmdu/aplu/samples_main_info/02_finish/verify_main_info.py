from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name=None),
            pol=LocationItem(name='XIAMEN (CN)'),
            pod=LocationItem(name='LOS ANGELES, CA (US)'),
            final_dest=LocationItem(name=None),
            eta=None,
            ata='Thu 25 Jul 2019 19:14',
        )

        assert results[1] == ContainerItem(
            container_no='TCLU9692715',
        )

        assert results[2] == ContainerStatusItem(
            container_no='TCLU9692715',
            local_date_time='Wed 03 Jul 2019 07:21',
            description='Empty to shipper',
            location=LocationItem(name='XIAMEN'),
            est_or_actual='A',
        )

        assert results[7] == ContainerStatusItem(
            container_no='TCLU9692715',
            local_date_time='Fri 02 Aug 2019 14:15',
            description='Empty in depot',
            location=LocationItem(name='LOS ANGELES, CA'),
            est_or_actual='A'
        )
