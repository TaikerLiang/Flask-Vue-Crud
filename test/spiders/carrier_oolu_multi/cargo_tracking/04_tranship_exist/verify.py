from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == {'date': '27 Nov 2019, 10:52  Local', 'status': 'Submitted'}
    assert results[1] == {
        'ata': '',
        'atd': '27 Nov 2019, 09:44 VNT',
        'deliv_ata': '',
        'deliv_eta': '24 Dec 2019, 08:00 CST',
        'eta': '16 Dec 2019, 15:30 PST',
        'etd': None,
        'final_dest': 'Dallas, Dallas, Texas, United States',
        'place_of_deliv': 'BNSF - Alliance',
        'pod': 'Long Beach, Los Angeles, California, United States',
        'pol': 'Hai Phong, Vietnam',
        'por': 'Hai Phong, Vietnam',
        'vessel': 'CSCL BOHAI SEA',
        'voyage': '032E'
    }
