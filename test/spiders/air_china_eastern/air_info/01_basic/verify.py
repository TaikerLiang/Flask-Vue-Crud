from crawler.core_air.items import AirItem


def verify(results):
    assert results[0] == AirItem(
        mawb='81231625',
        task_id='1',
        origin='LAX',
        destination='PVG',
        pieces=7,
        weight='3675 K',
        current_state='DLV',
    )

