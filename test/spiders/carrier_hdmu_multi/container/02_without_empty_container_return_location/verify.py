from crawler.core_carrier.items import LocationItem, ContainerItem, ContainerStatusItem, MblItem


def verify(results):
    assert results[0] == MblItem(task_id="1")

    assert results[1] == ContainerItem(
        container_key="KOCU4954805",
        container_no="KOCU4954805",
        last_free_day=None,
        mt_location=LocationItem(name=None),
        det_free_time_exp_date=None,
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="KOCU4954805",
        description="Import Empty Container Returned",
        local_date_time="13-Oct-2021 2:09 PM",
        location=LocationItem(name="MANILA, PHILIPPINES"),
        transport="Truck",
        task_id="1",
    )

    assert results[6] == ContainerStatusItem(
        container_key="KOCU4954805",
        description="Vessel Arrival at POD",
        local_date_time="30-Sep-2021 12:06 PM",
        location=LocationItem(name="MANILA, PHILIPPINES"),
        transport="GREEN OCEAN 0046S",
        task_id="1",
    )

    assert results[7] == ContainerStatusItem(
        container_key="KOCU4954805",
        description="Vessel Departure from T/S Port",
        local_date_time="28-Sep-2021 3:07 AM",
        location=LocationItem(name="KAOHSIUNG, TAIWAN, CHINA"),
        transport="GREEN OCEAN 0046S",
        task_id="1",
    )
