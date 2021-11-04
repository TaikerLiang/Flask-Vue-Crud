from typing import List

from crawler.core_air.items import AirItem, HistoryItem


def verify(results: List):
    assert results[0] == AirItem(
        task_id="1",
        mawb="66323191",
        origin="GUANGZHOU",
        destination="NASHVILLE",
        pieces="6",
        weight="1935",
        atd="2021-08-05 14:14:06",
        ata="2021-08-10 04:47:00",
    )

    assert results[1] == HistoryItem(
        task_id="1",
        status="Air Waybill has been received.",
        pieces="",
        weight="",
        time="2021-08-03 18:18:22",
        location="GUANGZHOU",
        flight_number="",
    )

    assert results[2] == HistoryItem(
        task_id="1",
        status="Cargo has been received.",
        pieces="6",
        weight="1935",
        time="2021-08-03 18:18:22",
        location="GUANGZHOU",
        flight_number="",
    )

    assert results[3] == HistoryItem(
        task_id="1",
        status="Cargo has been loaded.",
        pieces="6",
        weight="1935",
        time="2021-08-05 14:14:06",
        location="GUANGZHOU",
        flight_number="CZ473",
    )

    assert results[4] == HistoryItem(
        task_id="1",
        status="Flight has taken off.",
        pieces="",
        weight="",
        time="2021-08-05 14:14:06",
        location="GUANGZHOU",
        flight_number="CZ473",
    )

    assert results[5] == HistoryItem(
        task_id="1",
        status="Cargo has been received.",
        pieces="6",
        weight="1935",
        time="2021-08-05 19:10:00",
        location="LOSANGELES",
        flight_number="",
    )

    assert results[6] == HistoryItem(
        task_id="1",
        status="Air Waybill has been received.",
        pieces="",
        weight="",
        time="2021-08-05 19:10:00",
        location="LOSANGELES",
        flight_number="",
    )

    assert results[7] == HistoryItem(
        task_id="1",
        status="Cargo has been loaded.",
        pieces="6",
        weight="1935",
        time="2021-08-07 08:00:00",
        location="LOSANGELES",
        flight_number="BN0001T",
    )

    assert results[8] == HistoryItem(
        task_id="1",
        status="Flight has taken off.",
        pieces="",
        weight="",
        time="2021-08-07 08:00:00",
        location="LOSANGELES",
        flight_number="BN0001T",
    )

    assert results[9] == HistoryItem(
        task_id="1",
        status="Cargo has been received.",
        pieces="6",
        weight="1935",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_number="",
    )

    assert results[10] == HistoryItem(
        task_id="1",
        status="Delivery notification has been issued.",
        pieces="",
        weight="",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_number="",
    )

    assert results[11] == HistoryItem(
        task_id="1",
        status="Air Waybill has been received.",
        pieces="",
        weight="",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_number="",
    )

    assert results[12] == HistoryItem(
        task_id="1",
        status="Cargo has been picked up by BNA",
        pieces="6",
        weight="1935",
        time="2021-09-02 08:08:00",
        location="NASHVILLE",
        flight_number="",
    )
