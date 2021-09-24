from crawler.core_air.items import AirItem


def verify(results):
    assert results[0] == AirItem(
        mawb='28809955',
        origin='HKG',
        destination='LAX',
        pieces=208,
        weight=2533,
        current_state='DLV',
        ata='2021/07/26 07:39',
        atd='2021/07/25 18:02',
    )


