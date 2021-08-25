
from crawler.core_carrier.oney_smlm_multi_share_spider import Restart


def verify(results):
    assert results[0] == Restart(reason='IP block', search_no=['DALA35925000', 'OB-21060019'], task_id=[1, 2])
