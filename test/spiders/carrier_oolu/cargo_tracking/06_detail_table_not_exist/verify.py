from crawler.core_carrier.items_new import LocationItem, MblItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no="2650422090",
        vessel=None,
        voyage=None,
        por=LocationItem(name=None),
        pol=LocationItem(name=None),
        pod=LocationItem(name=None),
        etd=None,
        atd=None,
        eta=None,
        ata=None,
        place_of_deliv=LocationItem(name=None),
        deliv_eta=None,
        deliv_ata=None,
        final_dest=LocationItem(name=None),
        customs_release_status="Cleared",
        customs_release_date="25 Nov 2020, 19:30 GMT",
    )
