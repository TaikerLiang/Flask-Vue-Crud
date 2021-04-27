from typing import List

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no='W470030608',
        por=LocationItem(name='PORT KLANG, Malaysia'),
        pol=LocationItem(name='PORT KLANG, Malaysia'),
        pod=LocationItem(name='LOS ANGELES, CA, USA'),
        place_of_deliv=LocationItem(name='LOS ANGELES, CA, USA'),
        etd='2020/10/28 00:00',
        atd=None,
        eta=None,
        ata=None,
        firms_code='Y258',
        carrier_status='Steamship Release',
        carrier_release_date='2020/11/24 20:58',
        customs_release_status='Customs Release',
        customs_release_date='2020/11/25 20:15',
    )

    assert results[1] == ContainerItem(
        container_key='YMMU6022283',
        container_no='YMMU6022283',
        last_free_day=None,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        'https://www.yangming.com/e-service/Track_Trace/ctconnect.aspx?'
        'var=6kXS94MAUKku1eUXw6LbZNJ0Z7zsmCG2gMxvCuLaAXaCzPj2oJ%2fTFSGP'
        '4W%2fuEPFrf%2bRpGP2A14%2fOijvVSIl%2fMwRSFk1y%2f9V1iVuQOUyvPVnl'
        '87C8wrgwW09vNFy1Gdchyo4XiTcGIgO7w0JJ8p%2bnJZVKPokOBt3iE3TmiVstazA%3d'
    )

