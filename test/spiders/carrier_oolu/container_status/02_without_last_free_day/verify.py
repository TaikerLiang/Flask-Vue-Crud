from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='OOLU907741',
        container_no='OOLU907741',
        det_free_time_exp_date=None,
        last_free_day=None,
    )
