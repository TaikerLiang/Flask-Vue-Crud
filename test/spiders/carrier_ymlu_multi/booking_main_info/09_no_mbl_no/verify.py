from typing import List

from crawler.core_carrier.items import LocationItem, MblItem


def verify(results: List):
    assert results[0] == MblItem(
        booking_no="YLX400679",
        por=LocationItem(name="LONG BEACH, CA (USLGB)"),
        pol=LocationItem(name="LONG BEACH, CA (USLGB)"),
        pod=LocationItem(name="HONGKONG (HKHKG)"),
        place_of_deliv=LocationItem(name="HONG KONG (HKHKG)"),
        etd="2022/04/20 05:00",
        atd=None,
        eta=None,
        ata=None,
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        task_id=1,
        berthing_time=None,
        vessel="ONE OWL",
        voyage="018W (FP2152C)",
    )
