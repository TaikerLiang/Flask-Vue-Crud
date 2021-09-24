from crawler.core_air.items import AirItem


def verify(results):
    assert results[0] == AirItem(
        mawb='24413955',
        origin='TPE',
        destination='LAX',
        pieces=22,
        weight=5124,
        current_state='DLV',
        ata='2021/07/31 13:11',
        atd='2021/07/31 15:26',
    )

