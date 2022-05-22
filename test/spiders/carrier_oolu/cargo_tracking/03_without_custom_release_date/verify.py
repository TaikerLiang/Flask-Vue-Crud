from crawler.core_carrier.items_new import LocationItem, MblItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no="2628633440",
        vessel="APL MIAMI",
        voyage="0TU8ZE1MA",
        por=LocationItem(name="Lat Krabang, Thailand"),
        pol=LocationItem(name="Laem Chabang, Chon Buri, Thailand"),
        pod=LocationItem(name="Los Angeles, Los Angeles, California, United States"),
        etd=None,
        atd="22 Nov 2019, 15:17 THT",
        eta="12 Dec 2019, 18:00 PST",
        ata=None,
        place_of_deliv=LocationItem(name="Fenix Marine Services Los Angeles"),
        deliv_eta="16 Dec 2019, 08:00 PST",
        deliv_ata=None,
        final_dest=LocationItem(name="Los Angeles, Los Angeles, California, United States"),
        customs_release_status="Held",
        customs_release_date=None,
    )
