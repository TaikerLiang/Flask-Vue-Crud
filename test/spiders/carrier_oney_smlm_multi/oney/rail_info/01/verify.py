from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="BEAU5297455",
        ready_for_pick_up="Y",
        railway="OMAHA, NE, UNITED STATES",
        final_dest_eta="2019-09-29 21:40",
        task_id=1,
    )
