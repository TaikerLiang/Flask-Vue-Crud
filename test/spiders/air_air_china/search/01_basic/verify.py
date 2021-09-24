from typing import List

from crawler.core_air.items import AirItem, FlightItem


def verify(results: List):
    assert results[0] == AirItem(
        task_id="1",
        mawb="14426156",
        origin="JFK",
        destination="TAO",
        pieces="1pcs",
        weight="46kg",
        current_state="Current Cargo Status:DLV(Consignment physically delivered)--TAO(Qingdao/Liuting)--2021-07-30 08:59",
    )

    assert results[1] == FlightItem(
        task_id="1",
        flight_number="CA600/27JUL",
        origin="JFK",
        destination="TAO",
        pieces="1",
        weight="46",
        atd="2021-07-27 12:00",
        ata=None,
    )

    assert results[2] == FlightItem(
        task_id="1",
        flight_number="CA1579",
        origin="JFK",
        destination="TAO",
        pieces="1",
        weight="46",
        atd=None,
        ata="2021-07-29 16:52",
    )
