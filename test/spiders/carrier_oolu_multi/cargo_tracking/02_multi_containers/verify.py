from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='2109051600',
        vessel='EVER LEADER',
        voyage='0921E',
        por=LocationItem(name='Ningbo, Ningbo, Zhejiang, China'),
        pol=LocationItem(name='Ningbo, Ningbo, Zhejiang, China'),
        pod=LocationItem(name='Savannah, Chatham, Georgia, United States'),
        etd=None,
        atd='06 Oct 2019, 10:01 CCT',
        eta=None,
        ata='01 Nov 2019, 06:30 EDT',
        place_of_deliv=LocationItem(name='Norfolk Southern Corp - Austell'),
        deliv_eta=None,
        deliv_ata='03 Nov 2019, 19:26 EST',
        final_dest=LocationItem(name='Atlanta, Fulton, Georgia, United States'),
        customs_release_status='Cleared',
        customs_release_date='03 Nov 2019, 16:50 GMT',
        task_id=1,
    )
