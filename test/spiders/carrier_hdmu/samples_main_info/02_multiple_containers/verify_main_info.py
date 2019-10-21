from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.spiders.carrier_hdmu import FormDataFactory, UrlFactory
from test.spiders.utils import convert_formdata_to_bytes


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            mbl_no='QSWB8011462',
            por=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            pol=LocationItem(name='SHANGHAI,CHINA'),
            final_dest=LocationItem(name='LOS ANGELES, CA'),
            por_atd='27-Jun-2019 8:09 AM',
            ata='18-Jul-2019 4:48 AM',
            eta=None,
            atd='04-Jul-2019 12:30 PM',
            etd=None,
            us_ams_status='Filed',
            ca_aci_status=None,
            eu_ens_status=None,
            cn_cams_status=None,
            ja_afr_status=None,
            freight_status='Collected',
            us_customs_status='Cleared',
            deliv_order='Not Applicable',
            latest_update='Wednesday, July 31, 2019 6:42 AM',
            deliv_ata=None,
            pol_ata='03-Jul-2019 3:57 AM',
            firms_code='W185',
            freight_date='15-Jul-2019',
            us_customs_date='22-Jul-2019',
            bl_type='Way Bill',
            way_bill_status='Issued',
            way_bill_date='04-Jul-2019',
        )

        assert results[1] == VesselItem(
            vessel='HYUNDAI FAITH',
            voyage='082E',
            pol=LocationItem(name='SHANGHAI,CHINA'),
            pod=LocationItem(name='LOS ANGELES, CA'),
            ata='18-Jul-2019 4:48 AM',
            eta=None,
            atd='04-Jul-2019 12:30 PM',
            etd=None,
        )

        assert results[2] == ContainerItem(
            container_key='CAIU7469202',
            container_no='CAIU7469202',
            last_free_day='Gated-out',
            mt_location=LocationItem(name='APM TERMINALS (LOS ANGELES, CA)'),
            det_free_time_exp_date='02-Aug-2019',
            por_etd=None,
            pol_eta=None,
            final_dest_eta=None,
            ready_for_pick_up=None,
        )

        url_factory = UrlFactory()
        expect_url = url_factory.build_container_url(mbl_no='QSWB8011462')

        assert results[14].url == expect_url

        formdata_factory = FormDataFactory()
        expect_formdata = formdata_factory.build_container_formdata(mbl_no='QSWB8011462', container_index=4, h_num=-5)

        assert results[14].body == convert_formdata_to_bytes(expect_formdata)

        assert results[3] == ContainerStatusItem(
            container_key='CAIU7469202',
            container_no='CAIU7469202',
            description='Empty returned',
            local_date_time='29-Jul-2019 11:43 AM',
            location=LocationItem(name=None),
            transport=None,
        )

        assert results[5] == ContainerStatusItem(
            container_key='CAIU7469202',
            container_no='CAIU7469202',
            description='Discharged',
            local_date_time='21-Jul-2019 12:16 AM',
            location=LocationItem(name='LOS ANGELES, CA'),
            transport='HYUNDAI FAITH V 082E',
        )

        assert results[9] == ContainerStatusItem(
            container_key='CAIU7469202',
            container_no='CAIU7469202',
            description='Gate In loading port',
            local_date_time='03-Jul-2019 3:57 AM',
            location=LocationItem(name='SHANGHAI,CHINA'),
            transport='Truck',
        )
