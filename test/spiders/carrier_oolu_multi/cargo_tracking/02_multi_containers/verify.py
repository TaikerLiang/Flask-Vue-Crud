from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == {'date': '03 Nov 2019, 16:50 GMT', 'status': 'Cleared'}
    assert results[1] == {
        'ata': '01 Nov 2019, 06:30 EDT',
        'atd': '06 Oct 2019, 10:01 CCT',
        'deliv_ata': '03 Nov 2019, 19:26 EST',
        'deliv_eta': None,
        'eta': None,
        'etd': None,
        'final_dest': 'Atlanta, Fulton, Georgia, United States',
        'place_of_deliv': 'Norfolk Southern Corp - Austell',
        'pod': 'Savannah, Chatham, Georgia, United States',
        'pol': 'Ningbo, Ningbo, Zhejiang, China',
        'por': 'Ningbo, Ningbo, Zhejiang, China',
        'vessel': 'EVER LEADER',
        'voyage': '0921E'
    }
