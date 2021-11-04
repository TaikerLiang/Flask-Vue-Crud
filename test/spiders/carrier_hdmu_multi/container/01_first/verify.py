from crawler.core_carrier.items import LocationItem, ContainerItem, ContainerStatusItem, MblItem


def verify(results):

    assert results[0] == MblItem(task_id="1")

    assert results[1] == ContainerItem(
        container_key="HDMU6660528",
        container_no="HDMU6660528",
        last_free_day=None,
        mt_location=LocationItem(name="BARBOURS CUT TERMINAL (TAS)"),
        det_free_time_exp_date="18-Oct-2021",
        por_etd=None,
        pol_eta=None,
        final_dest_eta=None,
        ready_for_pick_up=None,
        task_id="1",
    )

    assert results[2] == ContainerStatusItem(
        container_key="HDMU6660528",
        description="Import Empty Container Returned",
        local_date_time="13-Oct-2021 4:07 PM",
        location=LocationItem(name="HOUSTON, TX"),
        transport="Truck",
        task_id="1",
    )

    assert results[4] == ContainerStatusItem(
        container_key="HDMU6660528",
        description="Vessel Unloading at POD",
        local_date_time="07-Oct-2021 4:10 AM",
        location=LocationItem(name="HOUSTON, TX"),
        transport="ONE MARVEL 0056E",
        task_id="1",
    )

    assert results[8] == ContainerStatusItem(
        container_key="HDMU6660528",
        description="Vessel Loading at POL",
        local_date_time="29-Aug-2021 7:14 PM",
        location=LocationItem(name="YANTIAN, SHENZHEN, CHINA"),
        transport="ONE MARVEL 0056E",
        task_id="1",
    )
