from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name=None),
            pol=LocationItem(name='NINGBO (CN)'),
            pod=LocationItem(name='LONG BEACH, CA (US)'),
            final_dest=LocationItem(name=None),
            eta='Thu 05 Sep 2019 04:30',
            ata=None,
        )

        assert results[1] == ContainerItem(
            container_no='ECMU9893257',
        )

        assert results[2] == ContainerStatusItem(
            container_no='ECMU9893257',
            local_date_time='Tue 13 Aug 2019 03:54',
            description='Empty to shipper',
            location=LocationItem(name='NINGBO'),
            est_or_actual='A',
        )

        assert results[5] == ContainerStatusItem(
            container_no='ECMU9893257',
            local_date_time='Thu 05 Sep 2019 04:30',
            description='Arrival final port of discharge',
            location=LocationItem(name='LONG BEACH, CA'),
            est_or_actual='E'
        )
