from typing import List

from crawler.core_carrier.items import ExportErrorData
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_ymlu_multi import BookingMainInfoPageRoutingRule


def verify(results: List):
    assert results[0] == ExportErrorData(
        task_id=1,
        booking_no='FCL147384',
        detail='Data was not found',
        status=CARRIER_RESULT_STATUS_ERROR,
    )

    assert results[1] == ExportErrorData(
        task_id=2,
        booking_no='FCL147097',
        detail='Data was not found',
        status=CARRIER_RESULT_STATUS_ERROR,
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].rule_name == BookingMainInfoPageRoutingRule.name

    follow_url = 'blconnect.aspx?var=iBc1aKoIXZsL8GIj08XKyupBIG8f9HaOD5fbPEBPqu5NQ3Q9W%2fsFNJ2uvGauNQLdMp5Ug1onSzMUg79GrjXHuxTrA199qiU%2fWVdpDW5t5KY%3d'
    assert results[2].url == f'https://www.yangming.com/e-service/Track_Trace/{follow_url}'
    assert results[2].meta['mbl_no'] == 'E144357267'
    assert results[2].meta['booking_no'] == 'YCH863258'
    assert results[2].meta['task_id'] == 3

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == BookingMainInfoPageRoutingRule.name

    follow_url = 'blconnect.aspx?var=rlCyFTxvCB7S4RUyJ0mJvexffX6JF56x85q5o7P6efZ%2fRXe3%2biAA62bPjiIBOZyDanFOy7armo2oA7JDzscGVAcmhvlB2YzGmLmvuohfOE4%3d'
    assert results[3].url == f'https://www.yangming.com/e-service/Track_Trace/{follow_url}'
    assert results[3].meta['mbl_no'] == 'W120511524'
    assert results[3].meta['booking_no'] == 'YCH857197'
    assert results[3].meta['task_id'] == 4
