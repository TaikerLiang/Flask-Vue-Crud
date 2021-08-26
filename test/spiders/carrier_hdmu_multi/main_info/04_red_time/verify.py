from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem


def verify(results):

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
        task_id='1',
    )

    assert results[1] == VesselItem(
        vessel_key='MAERSK ESSEX',
        vessel='MAERSK ESSEX',
        voyage='931N',
        pol=LocationItem(name='NINGBO, CHINA'),
        pod=LocationItem(name='LONG BEACH, CA'),
        ata=None,
        eta='23-Aug-2019 8:00 AM',
        atd=None,
        etd='07-Aug-2019 2:00 PM',
        task_id='1',
    )

    assert results[2] == ContainerItem(
        container_key='DFSU6966171',
        container_no='DFSU6966171',
        last_free_day=None,
        mt_location=LocationItem(name='TOTAL TERMINALS INTERNATIONAL - TTI (LONG BEACH, CA)'),
        det_free_time_exp_date=None,
        por_etd=None,
        pol_eta=None,
        final_dest_eta='23-Aug-2019 8:00 AM',
        ready_for_pick_up=None,
        task_id='1',
    )

    assert results[3] == ContainerStatusItem(
        container_key='DFSU6966171',
        description='Gate In loading port',
        local_date_time='02-Aug-2019 11:06 PM',
        location=LocationItem(name='NINGBO, CHINA'),
        transport='Truck',
        task_id='1',
    )
