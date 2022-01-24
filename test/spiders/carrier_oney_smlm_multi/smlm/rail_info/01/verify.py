from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="CCLU3451951",
        ready_for_pick_up="Y",
        railway="CN RAIL JOLIET",
        final_dest_eta="2019-09-27 01:54",
        task_id=1,
    )
