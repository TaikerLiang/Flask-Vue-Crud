from crawler.core_carrier.items import MblItem, VesselItem, ContainerItem, LocationItem, ContainerStatusItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):

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
        vessel_key='HYUNDAI CONFIDENCE',
        vessel='HYUNDAI CONFIDENCE',
        voyage='577E',
        pol=LocationItem(name='TAICHUNG, TAIWAN'),
        pod=LocationItem(name='TACOMA, WA'),
        ata='17-Apr-2019 4:18 AM',
        eta=None,
        atd='01-Apr-2019 10:30 AM',
        etd=None,
    )

    assert results[2] == ContainerItem(
        container_key='HMMU6015688',
        container_no='HMMU6015688',
        last_free_day='Gated-out',
        mt_location=LocationItem(name='M&N EQUIPMENT SERVICES ( EMPTIES ONLY) (MINNEAPOLIS, MN)'),
        det_free_time_exp_date='09-May-2019',
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
    )

    assert results[3] == ContainerStatusItem(
        container_key='HMMU6015688',
        description='Empty returned',
        local_date_time='03-May-2019 1:23 PM',
        location=LocationItem(name=None),
        transport=None,
    )

    assert results[19] == ContainerStatusItem(
        container_key='HMMU6015688',
        description='Discharged',
        local_date_time='17-Apr-2019 2:40 PM',
        location=LocationItem(name='TACOMA, WA'),
        transport='HYUNDAI CONFIDENCE V 577E',
    )

    assert results[23] == ContainerStatusItem(
        container_key='HMMU6015688',
        description='Inland transportation started',
        local_date_time='29-Mar-2019 2:11 PM',
        location=LocationItem(name='TAICHUNG, TAIWAN'),
        transport='Truck',
    )

    assert isinstance(results[26], RequestOption)
    assert results[26].url == 'http://www.hmm21.com/_/ebiz/track_trace/WUTInfo.jsp'
    assert results[26].meta['container_no'] == 'HMMU6015688'
