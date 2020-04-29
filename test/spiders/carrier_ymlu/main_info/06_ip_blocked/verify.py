from typing import List

from crawler.spiders.carrier_ymlu import Resent


def verify(results: List):
    assert isinstance(results[0], Resent)
    assert results[0].option.url == (
        'https://www.yangming.com/e-service/Track_Trace/blconnect.aspx?BLADG=E209048375,&rdolType=BL&type=cargo'
    )

