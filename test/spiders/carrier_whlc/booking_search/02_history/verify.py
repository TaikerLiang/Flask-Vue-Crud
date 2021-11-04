from typing import List


def verify(results: List):
    assert results[0] == ({
        'description': 'EMPTY CONTAINER DISCHARGED FROM VESSEL OR GATE IN TO PIER/TERMINAL/OFF-DOCK DEPOT (EMPTY AVAILABLE)',
        'local_date_time': '2021/08/24 12:10',
        'location_name': 'Oakland International Container Terminal; OICT (Berth 57-59) ; SSA Marine'
    })

    assert results[1] == ({
        'description': 'Full container withdrawn by consignee from Pier/Terminal',
        'local_date_time': '2021/08/23 14:50',
        'location_name': 'Oakland International Container Terminal; OICT (Berth 57-59) ; SSA Marine'
    })

    assert results[2] == ({
        'description': 'Full container(FCL) discharged from vessel OR GATE IN to Pier/Terminal',
        'local_date_time': '2021/08/14 08:46',
        'location_name': 'Oakland International Container Terminal; OICT (Berth 57-59) ; SSA Marine'})

    assert results[9] == ({
        'description': 'Full container withdrawn by consignee from Pier/Terminal',
        'local_date_time': '2021/07/24 15:04',
        'location_name': 'QINGDAO QIANWAN CTNR TERMINAL CO,LTD.'})