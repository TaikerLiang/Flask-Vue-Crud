from crawler.core_carrier.items import VesselItem


def verify(results):
    assert results[0] == VesselItem(task_id=1, vessel_key="")
