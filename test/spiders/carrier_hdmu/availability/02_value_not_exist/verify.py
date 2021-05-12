from crawler.core_carrier.items import ContainerItem


def verify(results):

    assert results[0] == ContainerItem(
        container_key='BMOU4101393',
        ready_for_pick_up=None,
    )
