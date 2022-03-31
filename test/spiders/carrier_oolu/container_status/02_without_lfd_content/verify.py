from crawler.core_carrier.items_new import ContainerItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="OOLU9077417",
        container_no="OOLU9077417",
        det_free_time_exp_date=None,
        last_free_day=None,
        terminal_pod=LocationItem(name=None),
        terminal_final_dest=LocationItem(name=None),
    )
