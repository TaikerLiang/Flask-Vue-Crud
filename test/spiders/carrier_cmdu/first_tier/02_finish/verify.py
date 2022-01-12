from typing import List

from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Wed 03 Jul 2019 08:38",
    )

    assert results[1] == ContainerItem(
        container_key="TRLU6600099",
        container_no="TRLU6600099",
    )

    assert results[2] == ContainerStatusItem(
        container_key="TRLU6600099",
        local_date_time="Tue 28 May 2019 12:38",
        description="Empty in depot",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
    )

    assert results[8] == ContainerStatusItem(
        container_key="TRLU6600099",
        local_date_time="Tue 09 Jul 2019 08:21",
        description="Off hire empty",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="A",
        facility="CONGLOBAL INDUSTRIES (CA)",
    )


def multi_verify(results: List):
    results.pop(0)

    assert results[0] == MblItem(
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (CN)"),
        pod=LocationItem(name="LOS ANGELES, CA (US)"),
        final_dest=LocationItem(name=None),
        eta=None,
        ata="Wed 03 Jul 2019 08:38",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="TRLU6600099",
        container_no="TRLU6600099",
        task_id=1,
    )

    assert results[2] == ContainerStatusItem(
        container_key="TRLU6600099",
        local_date_time="Tue 28 May 2019 12:38",
        description="Empty in depot",
        location=LocationItem(name="NINGBO"),
        est_or_actual="A",
        facility="",
        task_id=1,
    )

    assert results[8] == ContainerStatusItem(
        container_key="TRLU6600099",
        local_date_time="Tue 09 Jul 2019 08:21",
        description="Off hire empty",
        location=LocationItem(name="LOS ANGELES, CA"),
        est_or_actual="A",
        facility="CONGLOBAL INDUSTRIES (CA)",
        task_id=1,
    )
