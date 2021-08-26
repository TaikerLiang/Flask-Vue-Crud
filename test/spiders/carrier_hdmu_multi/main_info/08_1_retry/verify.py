from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_hdmu_multi import MainRoutingRule


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].url == 'http://www.hmm21.com/_/ebiz/track_trace/trackCTP_nTmp.jsp'
    assert results[0].rule_name == MainRoutingRule.name
    assert results[0].body == 'number=QSWB801163&type=1&selectedContainerIndex=&is_quick=Y&blFields=3&cnFields=3&numbers=QSWB801163&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers='

