from crawler.core_carrier.items_new import LocationItem, MblItem


def verify(item):
    assert item == MblItem(
        mbl_no="6199589860",
        vessel="CMA CGM TAGE",
        voyage="0TU5VE1MA",
        por=LocationItem(name="Jakarta ,Jakarta Raya ,Indonesia"),
        pol=LocationItem(name="Jakarta - JICT.1 (UTC-1)"),
        pod=LocationItem(
            name="Los Angeles - American President Line",
            firms_code=None,
        ),
        final_dest=LocationItem(
            name="Los Angeles ,California ,United States-American President Line",
            firms_code=None,
        ),
        place_of_deliv=LocationItem(
            name="Los Angeles ,California ,United States-American President Line",
            firms_code=None,
        ),
        etd=None,
        atd="2019-05-08 08:03",
        eta=None,
        ata="2019-05-30 17:02",
        bl_type="Sea WayBill",
        deliv_eta="2019-05-31 22:00",
        cargo_cutoff_date="2019-05-03 00:00",
        surrendered_status="Sea Waybill",
    )

    # assert results[1] == VesselItem(**{
    #     'vessel_key': 'CMA CGM TAGE',
    #     'vessel': 'CMA CGM TAGE',
    #     'voyage': '0TU5VE1MA',
    #     'pol': LocationItem(**{'name': 'Jakarta'}),
    #     'pod': LocationItem(**{'name': 'Los Angeles'}),
    #     'etd': '2019-05-07 12:00',
    #     'atd': '2019-05-08 08:03',
    #     'eta': '2019-05-30 18:00',
    #     'ata': '2019-05-30 17:02',
    #     'discharge_date': '2019-06-01 15:19',
    #     'shipping_date': '2019-05-07 23:00',
    #     'row_no': '1',
    #     'sequence_no': '1',
    # })
    #
    # assert results[2] == ContainerItem(**{
    #     'container_key': 'CSNU627621',
    #     'last_free_day': '2019-06-05',
    #     'empty_pickup_date': None,
    #     'empty_return_date': '2019-06-06 13:14',
    #     'full_pickup_date': '2019-06-05 08:34',
    #     'full_return_date': '2019-05-04 21:46',
    #     'ams_release': 'Clear',
    #     'depot_last_free_day': None,
    # })
    #
    # assert isinstance(results[3], RequestOption)
