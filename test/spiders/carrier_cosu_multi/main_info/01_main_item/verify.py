from crawler.core_carrier.items import LocationItem, MblItem


def verify(item):
    assert item == MblItem(
        **{
            "mbl_no": "6199589860",
            "task_id": "1",
            "vessel": "CMA CGM TAGE",
            "voyage": "0TU5VE1MA",
            "por": LocationItem(**{"name": "Jakarta ,Jakarta Raya ,Indonesia"}),
            "pol": LocationItem(**{"name": "Jakarta - JICT.1 (UTC-1)"}),
            "pod": LocationItem(
                **{
                    "name": "Los Angeles - American President Line",
                    "firms_code": None,
                }
            ),
            "final_dest": LocationItem(
                **{
                    "name": "Los Angeles ,California ,United States-American President Line",
                    "firms_code": None,
                }
            ),
            "place_of_deliv": LocationItem(
                **{
                    "name": "Los Angeles ,California ,United States-American President Line",
                    "firms_code": None,
                }
            ),
            "etd": None,
            "atd": "2019-05-08 08:03",
            "eta": None,
            "ata": "2019-05-30 17:02",
            "bl_type": "Sea WayBill",
            "deliv_eta": "2019-05-31 22:00",
            "cargo_cutoff_date": "2019-05-03 00:00",
            "surrendered_status": "Sea Waybill",
        }
    )
