from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.spiders.carrier_hdmu import UrlFactory, FormDataFactory
from test.spiders.utils import convert_formdata_to_bytes


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            mbl_no='NXWB1903966',
            por=LocationItem(name='NINGBO, CHINA'),
            pol=LocationItem(name='NINGBO, CHINA'),
            pod=LocationItem(name='LONG BEACH, CA'),
            final_dest=LocationItem(name='LONG BEACH, CA'),
            por_atd='02-Aug-2019 4:23 AM',
            ata=None,
            eta='23-Aug-2019 8:00 AM',
            atd=None,
            etd='07-Aug-2019 2:00 PM',
            us_ams_status='Filed',
            ca_aci_status=None,
            eu_ens_status=None,
            cn_cams_status=None,
            ja_afr_status=None,
            freight_status='Not yet collected',
            us_customs_status='Not yet cleared',
            deliv_order='Not Applicable',
            latest_update='Thursday, August 8, 2019 5:51 AM',
            deliv_ata=None,
            pol_ata='02-Aug-2019 11:06 PM',
            firms_code='Z952',
            freight_date=None,
            us_customs_date=None,
            bl_type=None,
            way_bill_status=None,
            way_bill_date=None,
        )

        assert results[1] == VesselItem(
            vessel='MAERSK ESSEX',
            voyage='931N',
            pol=LocationItem(name='NINGBO, CHINA'),
            pod=LocationItem(name='LONG BEACH, CA'),
            ata=None,
            eta='23-Aug-2019 8:00 AM',
            atd=None,
            etd='07-Aug-2019 2:00 PM',
        )

        assert results[2] == ContainerItem(
            container_no='DFSU6966171',
            last_free_day=None,
            mt_location=LocationItem(name='TOTAL TERMINALS INTERNATIONAL - TTI (LONG BEACH, CA)'),
            det_free_time_exp_date=None,
            por_etd=None,
            pol_eta=None,
            final_dest_eta='23-Aug-2019 8:00 AM',
            ready_for_pick_up=None,
        )

        url_factory = UrlFactory()
        expect_url = url_factory.build_container_url(mbl_no='NXWB1903966')

        assert results[5].url == expect_url

        formdata_factory = FormDataFactory()
        expect_formdata = formdata_factory.build_container_formdata(mbl_no='NXWB1903966', container_index=1, h_num=-2)

        assert results[5].body == convert_formdata_to_bytes(expect_formdata)

        assert results[3] == ContainerStatusItem(
            container_no='DFSU6966171',
            description='Gate In loading port',
            local_date_time='02-Aug-2019 11:06 PM',
            location=LocationItem(name='NINGBO, CHINA'),
            transport='Truck',
        )
