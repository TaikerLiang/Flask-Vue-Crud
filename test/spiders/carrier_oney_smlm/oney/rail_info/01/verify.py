from crawler.core_carrier.items_new import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="BEAU5297455",
        ready_for_pick_up="Y",
    )
