from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.spiders.carrier_hdmu import UrlFactory, FormDataFactory
from test.spiders.utils import convert_formdata_to_bytes


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == MblItem(
            mbl_no='TAWB0789799',
            por=LocationItem(name='TAICHUNG, TAIWAN'),
            pol=LocationItem(name='TAICHUNG, TAIWAN'),
            pod=LocationItem(name='TACOMA, WA'),
            final_dest=LocationItem(name='MINNEAPOLIS, MN'),
            por_atd='22-Mar-2019 10:26 AM',
            ata='17-Apr-2019 4:18 AM',
            eta=None,
            atd='01-Apr-2019 10:30 AM',
            etd=None,
            us_ams_status='Filed',
            ca_aci_status=None,
            eu_ens_status=None,
            cn_cams_status=None,
            ja_afr_status=None,
            freight_status='Collected',
            us_customs_status='Cleared',
            deliv_order='Not Applicable',
            latest_update='Wednesday, August 7, 2019 11:04 AM',
            deliv_ata=None,
            pol_ata='25-Mar-2019 4:59 PM',
            firms_code='J828',
            freight_date=None,
            us_customs_date='21-Apr-2019',
            way_bill_status='Issued',
            way_bill_date='02-Apr-2019',
            bl_type='Way Bill',
        )

        assert results[1] == VesselItem(
            vessel='HYUNDAI CONFIDENCE',
            voyage='577E',
            pol=LocationItem(name='TAICHUNG, TAIWAN'),
            pod=LocationItem(name='TACOMA, WA'),
            ata='17-Apr-2019 4:18 AM',
            eta=None,
            atd='01-Apr-2019 10:30 AM',
            etd=None,
        )

        url_factory = UrlFactory()
        form_factory = FormDataFactory()
        formdata = form_factory.build_availability_formdata(mbl_no='TAWB0789799', container_no='HMMU6015688')
        formdata_bytes = convert_formdata_to_bytes(formdata)
        assert results[2].url == url_factory.build_availability_url()
        assert results[2].body == formdata_bytes

        assert results[3] == ContainerStatusItem(
            container_no='HMMU6015688',
            description='Empty returned',
            local_date_time='03-May-2019 1:23 PM',
            location=LocationItem(name=None),
            transport=None,
        )

        assert results[19] == ContainerStatusItem(
            container_no='HMMU6015688',
            description='Discharged',
            local_date_time='17-Apr-2019 2:40 PM',
            location=LocationItem(name='TACOMA, WA'),
            transport='HYUNDAI CONFIDENCE V 577E',
        )

        assert results[23] == ContainerStatusItem(
            container_no='HMMU6015688',
            description='Inland transportation started',
            local_date_time='29-Mar-2019 2:11 PM',
            location=LocationItem(name='TAICHUNG, TAIWAN'),
            transport='Truck',
        )
