from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem, ContainerStatusItem


def verify(results):

    assert results[0] == MblItem(
        mbl_no='TYWB0924004',
        por=LocationItem(name='TAOYUAN, TAIWAN'),
        pod=LocationItem(name='VANCOUVER, BC, CANADA'),
        pol=LocationItem(name='KAOHSIUNG, TAIWAN'),
        final_dest=LocationItem(name='VANCOUVER, BC, CANADA'),
        por_atd='09-Dec-2019 3:51 PM',
        ata='04-Jan-2020 11:12 PM',
        eta=None,
        atd='16-Dec-2019 4:36 AM',
        etd=None,
        us_ams_status='Filed',
        ca_aci_status='Filed',
        eu_ens_status=None,
        cn_cams_status=None,
        ja_afr_status=None,
        freight_status=None,
        us_customs_status=None,
        deliv_order=None,
        latest_update='Monday, January 6, 2020 8:45 AM',
        deliv_ata=None,
        pol_ata='13-Dec-2019 7:31 PM',
        firms_code=None,
        freight_date=None,
        us_customs_date=None,
        bl_type=None,
        way_bill_status=None,
        way_bill_date=None,
        task_id='1',
    )

    assert results[1] == VesselItem(
        vessel_key='HYUNDAI INTEGRAL',
        vessel='HYUNDAI INTEGRAL',
        voyage='089E',
        pol=LocationItem(name='KAOHSIUNG, TAIWAN'),
        pod=LocationItem(name='VANCOUVER, BC, CANADA'),
        ata='04-Jan-2020 11:12 PM',
        eta=None,
        atd='16-Dec-2019 4:36 AM',
        etd=None,
        task_id='1',
    )

    assert results[2] == ContainerItem(
        container_key='GAOU6191712',
        container_no='GAOU6191712',
        last_free_day=None,
        mt_location=LocationItem(name='TERMINAL SYSTEMS, INC.(TSI) (VANCOUVER, BC, CANADA)'),
        det_free_time_exp_date=None,
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
        task_id='1',
    )

    assert results[3] == ContainerStatusItem(
        container_key='GAOU6191712',
        description='Discharged',
        local_date_time='05-Jan-2020 7:31 AM',
        location=LocationItem(name='VANCOUVER, BC, CANADA'),
        transport='HYUNDAI INTEGRAL V 089E',
        task_id='1',
    )

    assert results[7] == ContainerStatusItem(
        container_key='GAOU6191712',
        description='Gate In loading port',
        local_date_time='13-Dec-2019 7:31 PM',
        location=LocationItem(name='KAOHSIUNG, TAIWAN'),
        transport='Truck',
        task_id='1',
    )

    assert results[10] == ContainerStatusItem(
        container_key='GAOU6191712',
        description='Released to the shipper for stuffing',
        local_date_time='09-Dec-2019 3:51 PM',
        location=LocationItem(name='TAOYUAN, TAIWAN'),
        transport='Truck',
        task_id='1',
    )
