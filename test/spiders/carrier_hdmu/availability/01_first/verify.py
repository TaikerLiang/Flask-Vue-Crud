from crawler.core_carrier.items import ContainerItem


def verify(results):

    assert results[0] == ContainerItem(
        container_key='CAIU7479659',
        ready_for_pick_up='Already picked up',
    )
