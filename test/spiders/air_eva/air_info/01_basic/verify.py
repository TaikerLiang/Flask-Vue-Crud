from crawler.core_air.items import AirItem
from crawler.core_air.request_helpers import RequestOption
from crawler.spiders.air_eva import DetailPageRoutingRule

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
    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DetailPageRoutingRule.name
    assert results[1].meta == {
        'mawb_no': '28809955',
    }
    assert results[1].url == 'https://www.brcargo.com/NEC_WEB/Tracking/QuickTracking/QuickTrackingDetail'


