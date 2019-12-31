from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.spiders.carrier_hdmu import AvailabilityRoutingRule


def verify(results):

    assert results[0] == MblItem(
        mbl_no='KETC0876470',
        por=LocationItem(name='KEELUNG, TAIWAN'),
        pol=LocationItem(name='KAOHSIUNG, TAIWAN'),
        pod=LocationItem(name='TACOMA, WA'),
        final_dest=LocationItem(name='TACOMA, WA'),
        por_atd='31-Jul-2019 4:55 PM',
        ata=None,
        eta='20-Aug-2019 5:00 PM',
        atd='06-Aug-2019 3:36 AM',
        etd=None,
        us_ams_status='Filed',
        ca_aci_status=None,
        eu_ens_status=None,
        cn_cams_status=None,
        ja_afr_status=None,
        freight_status='Collected',
        us_customs_status='Not yet cleared',
        deliv_order='Not Applicable',
        latest_update='Thursday, August 8, 2019 6:07 AM',
        deliv_ata=None,
        pol_ata='02-Aug-2019 8:30 PM',
        firms_code='Z705',
        freight_date=None,
        us_customs_date=None,
        bl_type=None,
        way_bill_status=None,
        way_bill_date=None,
    )

    assert results[1] == VesselItem(
        vessel_key='WIDE INDIA',
        vessel='WIDE INDIA',
        voyage='010N',
        pol=LocationItem(name='KAOHSIUNG, TAIWAN'),
        pod=LocationItem(name='TACOMA, WA'),
        ata=None,
        eta='20-Aug-2019 5:00 PM',
        atd='06-Aug-2019 3:36 AM',
        etd=None,
    )

    assert results[2] == ContainerItem(
        container_key='CAIU7479659',
        container_no='CAIU7479659',
        last_free_day=None,
        mt_location=LocationItem(name='WASHINGTON UNITED TERMINALS INC. (TACOMA, WA)'),
        det_free_time_exp_date=None,
        por_etd=None,
        pol_eta=None,
        final_dest_eta='20-Aug-2019 5:00 PM',
        ready_for_pick_up=None,
    )

    assert results[3] == AvailabilityRoutingRule.build_request_config(
        mbl_no='KETC0876470',
        container_no='CAIU7479659',
    )

    assert results[4] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Vessel Departed',
        local_date_time='06-Aug-2019 3:36 AM',
        location=LocationItem(name='KAOHSIUNG, TAIWAN'),
        transport='WIDE INDIA V 010N',
    )

    assert results[5] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Shipped on',
        local_date_time='05-Aug-2019 11:34 PM',
        location=LocationItem(name='KAOHSIUNG, TAIWAN'),
        transport='WIDE INDIA V 010N',
    )

    assert results[6] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Gate In loading port',
        local_date_time='02-Aug-2019 8:30 PM',
        location=LocationItem(name='KAOHSIUNG, TAIWAN'),
        transport='Truck',
    )

    assert results[7] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Inland transportation started',
        local_date_time='02-Aug-2019 1:58 PM',
        location=LocationItem(name='KEELUNG, TAIWAN'),
        transport='Truck',
    )

    assert results[8] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Gate in',
        local_date_time='31-Jul-2019 5:00 PM',
        location=LocationItem(name='KEELUNG, TAIWAN'),
        transport='Truck',
    )

    assert results[9] == ContainerStatusItem(
        container_key='CAIU7479659',
        description='Released to the shipper for stuffing',
        local_date_time='31-Jul-2019 4:55 PM',
        location=LocationItem(name='KEELUNG, TAIWAN'),
        transport='Truck',
    )
