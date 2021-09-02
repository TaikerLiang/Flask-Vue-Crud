from typing import List

from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_ymlu_multi import BookingMainInfoPageRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == BookingMainInfoPageRoutingRule.name
    follow_url = '/blconnect.aspx?var=rlCyFTxvCB7S4RUyJ0mJvexffX6JF56x85q5o7P6efasZNVyFPBsA5lbCrkJPto8lmbGdwy%2fciRgJoSkU85LARFdFoAibgS%2b6aAx4L0mYn%2flyMdRIv7PZ%2bIm9qCQ2UwV'
    assert results[0].url == f'https://www.yangming.com/e-service/Track_Trace/{follow_url}'
    assert results[0].meta['mbl_no'] == 'W120511524'
    assert results[0].meta['booking_no'] == 'YCH857197'
    assert results[0].meta['task_id'] == 1
