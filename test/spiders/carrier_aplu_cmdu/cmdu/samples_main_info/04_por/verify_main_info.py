from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            por=LocationItem(name='HUANGPU (CN)'),
            pol=LocationItem(name='NANSHA (CN)'),
            pod=LocationItem(name='OAKLAND, CA (US)'),
            final_dest=LocationItem(name=None),
            eta='Sat 31 Aug 2019 06:00',
            ata=None,
        )

        assert results[1] == ContainerItem(
            container_key='GLDU5292400',
            container_no='GLDU5292400',
        )

        assert results[2] == ContainerStatusItem(
            container_key='GLDU5292400',
            container_no='GLDU5292400',
            local_date_time='Mon 29 Jul 2019 14:51',
            description='Empty to shipper',
            location=LocationItem(name='HUANGPU'),
            est_or_actual='A',
        )

        assert results[7] == ContainerStatusItem(
            container_key='GLDU5292400',
            container_no='GLDU5292400',
            local_date_time='Sat 31 Aug 2019 06:00',
            description='Arrival final port of discharge',
            location=LocationItem(name='OAKLAND, CA'),
            est_or_actual='E'
        )
