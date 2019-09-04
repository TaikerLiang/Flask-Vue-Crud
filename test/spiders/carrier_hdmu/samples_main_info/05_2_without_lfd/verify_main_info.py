from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.spiders.carrier_hdmu import UrlFactory, FormDataFactory
from test.spiders.utils import convert_formdata_to_bytes


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            mbl_no='QSWB8011630',
            por=LocationItem(name='SHANGHAI,CHINA'),
            pol=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            final_dest=LocationItem(name='LOS ANGELES, CA'),
            por_atd='02-Aug-2019 6:02 AM',
            ata=None,
            eta='21-Aug-2019 5:00 PM',
            atd='08-Aug-2019 3:30 AM',
            etd=None,
            us_ams_status='Filed',
            ca_aci_status=None,
            eu_ens_status=None,
            cn_cams_status=None,
            ja_afr_status=None,
            freight_status='Not yet collected',
            us_customs_status='Not yet cleared',
            deliv_order='Not Applicable',
            latest_update='Thursday, August 8, 2019 6:57 AM',
            deliv_ata=None,
            pol_ata='06-Aug-2019 12:39 AM',
            firms_code='W185',
            freight_date=None,
            us_customs_date=None,
            bl_type='Way Bill',
            way_bill_status='Issued',
            way_bill_date='08-Aug-2019',
        )

        assert results[1] == VesselItem(
            vessel='HYUNDAI COURAGE',
            voyage='081E',
            pol=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            ata=None,
            eta='21-Aug-2019 5:00 PM',
            atd='08-Aug-2019 3:30 AM',
            etd=None,
        )

        assert results[2] == ContainerItem(
            container_no='TEMU7285430',
            last_free_day=None,
            mt_location=LocationItem(name='APM TERMINALS (LOS ANGELES, CA)'),
            det_free_time_exp_date=None,
            por_etd=None,
            pol_eta=None,
            final_dest_eta='21-Aug-2019 5:00 PM',
            ready_for_pick_up=None
        )

        url_factory = UrlFactory()
        expect_url = url_factory.build_container_url(mbl_no='QSWB8011630')

        assert results[16].url == expect_url

        formdata_factory = FormDataFactory()
        expect_formdata = formdata_factory.build_container_formdata(mbl_no='QSWB8011630', container_index=10, h_num=-11)

        assert results[16].body == convert_formdata_to_bytes(expect_formdata)

        assert results[3] == ContainerStatusItem(
            container_no='TEMU7285430',
            description='Vessel Departed',
            local_date_time='08-Aug-2019 3:30 AM',
            location=LocationItem(name='SHANGHAI,CHINA'),
            transport='HYUNDAI COURAGE V 081E',
        )

        assert results[5] == ContainerStatusItem(
            container_no='TEMU7285430',
            description='Gate In loading port',
            local_date_time='06-Aug-2019 12:39 AM',
            location=LocationItem(name='SHANGHAI,CHINA'),
            transport='Truck',
        )
