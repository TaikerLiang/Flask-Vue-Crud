from crawler.core_carrier.items_new import LocationItem, MblItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no="2630699272",
        vessel="CSCL BOHAI SEA",
        voyage="032E",
        por=LocationItem(name="Hai Phong, Vietnam"),
        pol=LocationItem(name="Hai Phong, Vietnam"),
        pod=LocationItem(name="Long Beach, Los Angeles, California, United States"),
        etd=None,
        atd="27 Nov 2019, 09:44 VNT",
        eta="16 Dec 2019, 15:30 PST",
        ata=None,
        place_of_deliv=LocationItem(name="BNSF - Alliance"),
        deliv_eta="24 Dec 2019, 08:00 CST",
        deliv_ata=None,
        final_dest=LocationItem(name="Dallas, Dallas, Texas, United States"),
        customs_release_status="Submitted",
        customs_release_date="27 Nov 2019, 10:52  Local",
    )
