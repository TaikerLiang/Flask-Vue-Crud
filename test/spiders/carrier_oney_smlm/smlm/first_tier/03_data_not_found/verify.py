from crawler.core_carrier.oney_smlm_share_spider import Restart


def verify(results):
    assert results[0] == Restart(reason='IP block')
