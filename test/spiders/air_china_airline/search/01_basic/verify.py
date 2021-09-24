from typing import List

from crawler.core_air.items import AirItem, FlightItem


def verify(results: List):
    assert results[0] == AirItem(
        task_id="1",
        mawb="14527634",
        origin="CAN",
        destination="LAX",
        pieces="5",
        weight="1088 KG",
        current_state="5pc(s)delivered to the consignee in LAX",
    )

    assert results[2] == FlightItem(
        task_id="1",
        flight_number="CI 5896",
        origin="CAN",
        destination="TPE",
        pieces="5",
        weight="1088 KG",
        atd="01Aug 02:22",
        ata="01Aug 04:22",
    )
