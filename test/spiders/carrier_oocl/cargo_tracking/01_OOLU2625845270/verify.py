from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='OOCL2625845270',
            por=LocationItem(name='Yantian, Shenzhen, Guangdong, China'),
            etd=None,
            atd='10 Sep 2019, 12:38 CCT',
            voyage='SC2 XIN YING KOU',
            vessel='089E',
            pod=LocationItem(name='Yantian, Shenzhen, Guangdong, China'),
            ata='28 Sep 2019, 06:10 PDT',
            eta=None,
            place_of_deliv=LocationItem(name='Long Beach, Los Angeles, California, United States'),
            deliv_ata='28 Sep 2019, 06:10 PDT',
            deliv_eta=None,
            final_dest=LocationItem(name='Chicago, Cook, Illinois, United States'),
        )
        assert results[1] == ContainerItem(
            container_no='OOCU808187-0',
            container_key='OOCU808187-0',
            last_free_day='09 Oct 2019, 23:59  Local',
            det_free_time_exp_date='21 Oct 2019, 23:59  Local',
        )
        assert results[2] == ContainerStatusItem(
            description='Container Returned to Carrier',
            location=LocationItem(name='CN Rail - Harvey, Chicago, Cook, Illinois, United States'),
            transport='Truck',
            local_date_time='08 Oct 2019, 08:54 CDT',
        )
