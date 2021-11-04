from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no="2635541720",
        vessel="NYK ALTAIR",
        voyage="049W",
        por=LocationItem(name="Los Angeles, Los Angeles, California, United States"),
        pol=LocationItem(name="Los Angeles, Los Angeles, California, United States"),
        pod=LocationItem(name="Kobe, Hyogo-ken, Japan"),
        etd=None,
        atd="01 Mar 2020, 05:02 PST",
        eta=None,
        ata="18 Mar 2020, 23:25 JPT",
        place_of_deliv=LocationItem(name="Nanko C-7"),
        deliv_eta=None,
        deliv_ata="24 Mar 2020, 08:19 JPT",
        final_dest=LocationItem(name="Osaka, Japan"),
        customs_release_status=None,
        customs_release_date=None,
        task_id="1",
    )
