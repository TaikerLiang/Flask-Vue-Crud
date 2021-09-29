from typing import List

from crawler.core_air.items import AirItem, HistoryItem


def verify(results: List):
    assert results[0] == AirItem(
        mawb="66323191",
        origin="GUANGZHOU",
        destination="NASHVILLE",
        pieces="6",
        weight="1935",
        atd="2021-08-05 14:14:06",
        ata="2021-08-10 04:47:00",
    )

    assert results[1] == HistoryItem(
        status="Air Waybill has been received.",
        Pieces="",
        Weight="",
        time="2021-08-03 18:18:22",
        location="GUANGZHOU",
        flight_no="",
    )

    assert results[2] == HistoryItem(
        status="Cargo has been received.",
        Pieces="6",
        Weight="1935",
        time="2021-08-03 18:18:22",
        location="GUANGZHOU",
        flight_no="",
    )

    assert results[3] == HistoryItem(
        status="Cargo has been loaded.",
        Pieces="6",
        Weight="1935",
        time="2021-08-05 14:14:06",
        location="GUANGZHOU",
        flight_no="CZ473",
    )

    assert results[4] == HistoryItem(
        status="Flight has taken off.",
        Pieces="",
        Weight="",
        time="2021-08-05 14:14:06",
        location="GUANGZHOU",
        flight_no="CZ473",
    )

    assert results[5] == HistoryItem(
        status="Cargo has been received.",
        Pieces="6",
        Weight="1935",
        time="2021-08-05 19:10:00",
        location="LOSANGELES",
        flight_no="",
    )

    assert results[6] == HistoryItem(
        status="Air Waybill has been received.",
        Pieces="",
        Weight="",
        time="2021-08-05 19:10:00",
        location="LOSANGELES",
        flight_no="",
    )

    assert results[7] == HistoryItem(
        status="Cargo has been loaded.",
        Pieces="6",
        Weight="1935",
        time="2021-08-07 08:00:00",
        location="LOSANGELES",
        flight_no="BN0001T",
    )

    assert results[8] == HistoryItem(
        status="Flight has taken off.",
        Pieces="",
        Weight="",
        time="2021-08-07 08:00:00",
        location="LOSANGELES",
        flight_no="BN0001T",
    )

    assert results[9] == HistoryItem(
        status="Cargo has been received.",
        Pieces="6",
        Weight="1935",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_no="",
    )

    assert results[10] == HistoryItem(
        status="Delivery notification has been issued.",
        Pieces="",
        Weight="",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_no="",
    )

    assert results[11] == HistoryItem(
        status="Air Waybill has been received.",
        Pieces="",
        Weight="",
        time="2021-08-10 04:47:00",
        location="NASHVILLE",
        flight_no="",
    )

    assert results[12] == HistoryItem(
        status="Cargo has been picked up by BNA",
        Pieces="6",
        Weight="1935",
        time="2021-09-02 08:08:00",
        location="NASHVILLE",
        flight_no="",
    )
