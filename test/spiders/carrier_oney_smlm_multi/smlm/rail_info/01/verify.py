from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='CCLU3451951',
        ready_for_pick_up='Y',
        task_id=1,
    )
