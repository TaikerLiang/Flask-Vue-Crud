from typing import List

from crawler.core_air.items import AirItem, HistoryItem


def verify(results: List):
    assert results[0] == AirItem(
        mawb='81231625',
        task_id='1',
        origin='LAX',
        destination='PVG',
        pieces=7,
        weight='3675 K',
        current_state='DLV',
    )
    assert results[1] == HistoryItem(
        task_id='1',
        status="Booked",
        pieces=7,
        weight="367",
        time="18 Sep 03:56",
        location="LAX",
        flight_number="CK222",
    )
    assert results[2] == HistoryItem(
        task_id='1',
        status="Booked",
        pieces=7,
        weight="367",
        time="18 Sep 06:21",
        location="LAX",
        flight_number="CK222",
    )
    assert results[22] == HistoryItem(
        task_id='1',
        status="Consignee notified - hold for pick-up",
        pieces=7,
        weight="3675",
        time="22 Sep 08:56",
        location="PVG",
        flight_number="",
    )
    assert results[23] == HistoryItem(
        task_id='1',
        status="Arrived",
        pieces=7,
        weight="3675",
        time="22 Sep 08:56",
        location="PVG",
        flight_number="CK222",
    )
    assert results[24] == HistoryItem(
        task_id='1',
        status="Delivered",
        pieces=7,
        weight="3675",
        time="23 Sep 14:59",
        location="PVG",
        flight_number="",
    )
