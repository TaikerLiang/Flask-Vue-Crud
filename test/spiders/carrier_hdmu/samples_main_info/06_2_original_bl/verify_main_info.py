from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            mbl_no='QSLB8267628',
            por=LocationItem(name='SHANGHAI,CHINA'),
            pol=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            final_dest=LocationItem(name='LOS ANGELES, CA'),
            por_atd='26-Jul-2019 7:52 PM',
            ata='14-Aug-2019 2:42 PM',
            eta=None,
            atd='01-Aug-2019 11:00 AM',
            etd=None,
            us_ams_status='Filed',
            ca_aci_status=None,
            eu_ens_status=None,
            cn_cams_status=None,
            ja_afr_status=None,
            freight_status='Collected',
            us_customs_status='Cleared',
            deliv_order='Not Applicable',
            latest_update='Tuesday, August 20, 2019 7:01 AM',
            deliv_ata=None,
            pol_ata='27-Jul-2019 3:46 PM',
            firms_code='W185',
            freight_date=None,
            us_customs_date='09-Aug-2019',
            bl_type=None,
            way_bill_status=None,
            way_bill_date=None,
        )

        assert results[1] == VesselItem(
            vessel='HYUNDAI BRAVE',
            voyage='079E',
            pol=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            ata='14-Aug-2019 2:42 PM',
            eta=None,
            atd='01-Aug-2019 11:00 AM',
            etd=None,
        )

        assert results[2] == ContainerItem(
            container_key='HDMU2752605',
            container_no='HDMU2752605',
            last_free_day='21-Aug-2019',
            mt_location=LocationItem(name='APM TERMINALS (LOS ANGELES, CA)'),
            det_free_time_exp_date=None,
            por_etd=None,
            pol_eta=None,
            final_dest_eta=None,
            ready_for_pick_up=None,
        )

        assert results[3] == ContainerStatusItem(
            container_key='HDMU2752605',
            container_no='HDMU2752605',
            description='Discharged',
            local_date_time='16-Aug-2019 12:24 AM',
            location=LocationItem(name='LOS ANGELES, CA'),
            transport='HYUNDAI BRAVE V 079E',
        )

        assert results[5] == ContainerStatusItem(
            container_key='HDMU2752605',
            container_no='HDMU2752605',
            description='Vessel Departed',
            local_date_time='01-Aug-2019 11:00 AM',
            location=LocationItem(name='SHANGHAI,CHINA'),
            transport='HYUNDAI BRAVE V 079E',
        )

        assert results[7] == ContainerStatusItem(
            container_key='HDMU2752605',
            container_no='HDMU2752605',
            description='Gate In loading port',
            local_date_time='27-Jul-2019 3:46 PM',
            location=LocationItem(name='SHANGHAI,CHINA'),
            transport='Truck',
        )
