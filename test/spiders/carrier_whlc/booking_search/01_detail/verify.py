from typing import List

def verify_basic(results):
    assert results == {
        'vessel': 'BOX ENDEAVOUR',
        'voyage': 'E120'
    }

def verify_vessel(results):
    assert results == {'eta': '2021/07/31',
         'etd': '2021/08/12',
         'place_of_deliv': 'OAKLAND, CA (US)',
         'pod': 'OAKLAND, CA (US)',
         'pol': 'QINGDAO (CN)',
         'por': 'QINGDAO (CN)'
    }


def verify_container_no(results: List):
    assert results[0] == 'TCKU7313477'
    assert results[1] == 'TGHU6447246'