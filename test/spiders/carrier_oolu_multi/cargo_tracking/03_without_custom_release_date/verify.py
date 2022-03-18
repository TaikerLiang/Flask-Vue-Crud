from crawler.core_carrier.items import MblItem, LocationItem


def verify(results):
    assert results[0] == {'date': '', 'status': 'Held'}
    assert results[1] == {
        'ata': '',
        'atd': '22 Nov 2019, 15:17 THT',
        'deliv_ata': '',
        'deliv_eta': '16 Dec 2019, 08:00 PST',
        'eta': '12 Dec 2019, 18:00 PST',
        'etd': None,
        'final_dest': 'Los Angeles, Los Angeles, California, United States',
        'place_of_deliv': 'Fenix Marine Services Los Angeles',
        'pod': 'Los Angeles, Los Angeles, California, United States',
        'pol': 'Laem Chabang, Chon Buri, Thailand',
        'por': 'Lat Krabang, Thailand',
        'vessel': 'APL MIAMI',
        'voyage': '0TU8ZE1MA'
    }
