from crawler.core_air.items import HistoryItem


def verify(results):
    assert results[0] == HistoryItem(
        status='DLV',
        pieces=188,
        weight=0,
        flight_number='',
        location='LAX',
        time='2021/07/28 18:34',
    )
    assert results[1] == HistoryItem(
        status='DLV',
        pieces=208,
        weight=0,
        flight_number='',
        location='LAX',
        time='2021/07/28 18:34',
    )
    assert results[2] == HistoryItem(
        status='ARR',
        pieces=208,
        weight=2533,
        flight_number='BR0006',
        location='LAX',
        time='2021/07/26 07:39',
    )
    assert results[3] == HistoryItem(
        status='RCF',
        pieces=208,
        weight=2533,
        flight_number='BR0006',
        location='LAX',
        time='2021/07/26 07:29',
    )
    assert results[4] == HistoryItem(
        status='DEP',
        pieces=208,
        weight=2533,
        flight_number='BR0006',
        location='TPE',
        time='2021/07/26 10:04',
    )
    assert results[5] == HistoryItem(
        status='RCF',
        pieces=208,
        weight=2533,
        flight_number='BR0828',
        location='TPE',
        time='2021/07/25 22:00',
    )
    assert results[6] == HistoryItem(
        status='ARR',
        pieces=208,
        weight=2533,
        flight_number='BR0828',
        location='TPE',
        time='2021/07/25 19:44',
    )
    assert results[7] == HistoryItem(
        status='DEP',
        pieces=208,
        weight=2533,
        flight_number='BR0828',
        location='HKG',
        time='2021/07/25 18:02',
    )
    assert results[8] == HistoryItem(
        status='RCS',
        pieces=208,
        weight=2533,
        flight_number='',
        location='HKG',
        time='2021/07/25 17:17',
    )
    assert results[9] == HistoryItem(
        status='BKD',
        pieces=208,
        weight=2533,
        flight_number='BR0006',
        location='HKG',
        time='2021/07/24 14:33',
    )
    assert results[10] == HistoryItem(
        status='BKD',
        pieces=208,
        weight=2533,
        flight_number='BR0828',
        location='HKG',
        time='2021/07/24 14:33',
    )

