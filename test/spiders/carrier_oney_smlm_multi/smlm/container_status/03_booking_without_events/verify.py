from crawler.core_carrier.oney_smlm_multi_share_spider import Restart


def verify(results):
    assert results == [Restart(reason="No container status info", search_nos=["NJPU9A246200"], task_ids=[1])]
