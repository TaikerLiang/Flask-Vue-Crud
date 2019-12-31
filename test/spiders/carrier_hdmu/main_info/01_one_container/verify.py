from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem


def verify(results):

    assert results[0] == MblItem(
        mbl_no='GJWB1899760',
        por=LocationItem(name='YANTIAN, SHENZHEN, CHINA'),
        pod=LocationItem(name='LOS ANGELES, CA'),
        pol=LocationItem(name='YANTIAN, SHENZHEN, CHINA'),
        final_dest=LocationItem(name='LOS ANGELES, CA'),
        por_atd='18-Apr-2019 7:38 AM',
        ata='14-May-2019 4:20 AM',
        eta=None,
        atd='29-Apr-2019 11:30 PM',
        etd=None,
        us_ams_status='Filed',
        ca_aci_status=None,
        eu_ens_status=None,
        cn_cams_status=None,
        ja_afr_status=None,
        freight_status='Collected',
        us_customs_status='Cleared',
        deliv_order='Not Applicable',
        latest_update='Wednesday, July 31, 2019 6:46 AM',
        deliv_ata=None,
        pol_ata='19-Apr-2019 11:18 AM',
        firms_code='W185',
        freight_date='15-May-2019',
        us_customs_date='13-May-2019',
        bl_type='Way Bill',
        way_bill_status='Issued',
        way_bill_date='07-May-2019',
    )

    assert results[1] == VesselItem(
        vessel_key='MAERSK ENSENADA',
        vessel='MAERSK ENSENADA',
        voyage='917N',
        pol=LocationItem(name='YANTIAN, SHENZHEN, CHINA'),
        pod=LocationItem(name='LOS ANGELES, CA'),
        ata='14-May-2019 4:20 AM',
        eta=None,
        atd='29-Apr-2019 11:30 PM',
        etd=None,
    )

    assert results[2] == ContainerItem(
        container_key='HDMU6681135',
        container_no='HDMU6681135',
        last_free_day='Gated-out',
        mt_location=LocationItem(name='APM TERMINALS (LOS ANGELES, CA)'),
        det_free_time_exp_date='08-Jun-2019',
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
    )

    assert results[3] == ContainerStatusItem(
        container_key='HDMU6681135',
        description='Empty returned',
        local_date_time='24-May-2019 8:54 AM',
        location=LocationItem(name=None),
        transport=None,
    )

    assert results[5] == ContainerStatusItem(
        container_key='HDMU6681135',
        description='Discharged',
        local_date_time='18-May-2019 12:50 AM',
        location=LocationItem(name='LOS ANGELES, CA'),
        transport='MAERSK ENSENADA V 917N',
    )

    assert results[9] == ContainerStatusItem(
        container_key='HDMU6681135',
        description='Gate In loading port',
        local_date_time='19-Apr-2019 11:18 AM',
        location=LocationItem(name='YANTIAN, SHENZHEN, CHINA'),
        transport='Truck',
    )
