from crawler.core_carrier.items_new import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
)


def verify(results):
    assert results[0] == ContainerItem(
        container_key="OOLU1213862",
        container_no="OOLU1213862",
        det_free_time_exp_date=None,
        last_free_day=None,
    )

    assert results[1] == ContainerStatusItem(
        container_key="OOLU1213862",
        description="Vessel Departed (Port of Load)",
        location=LocationItem(name="Long Beach, Long Beach, Los Angeles, California, United States"),
        transport=None,
        local_date_time="15 Dec 2019, 06:18 PST",
    )
