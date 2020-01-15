from crawler.core_carrier.items import ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key='CRSU9164589',
        container_no='CRSU9164589',
    )

    assert results[1] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='Discharged from vessel ATLANTIC SAIL /8262 at Halifax-Ceres Terminal,Nova Scotia,Canada',
        location=LocationItem(name='Halifax-Ceres Terminal,Nova Scotia,Canada'),
        local_date_time='01/31/18 08:30',
        vessel='ATLANTIC SAIL /8262',
    )

    assert results[2] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='The ETA at the port of Discharge will be',
        location=LocationItem(name='Halifax-Ceres Terminal,Nova Scotia,Canada'),
        local_date_time='01/31/18 08:00',
        vessel='ATLANTIC SAIL /8262',
    )

    assert results[3] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='which sailed on',
        location=LocationItem(name=None),
        local_date_time='01/22/18 12:36',
        vessel='ATLANTIC SAIL /8262',
    )

    assert results[4] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='Loaded full on vessel ATLANTIC SAIL /8262',
        location=LocationItem(name=None),
        local_date_time='01/22/18 05:47',
        vessel='ATLANTIC SAIL /8262',
    )

    assert results[6] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='Departed for Liverpool Seaforth,United Kingdom L21.1 for vessel ATLANTIC SAIL /8262',
        location=LocationItem(name='Liverpool Seaforth,United Kingdom L21.1'),
        local_date_time='01/17/18 19:27',
        vessel='ATLANTIC SAIL /8262',
    )

    assert results[7] == ContainerStatusItem(
        container_key='CRSU9164589',
        description='Received at Dublin-Port,Ireland',
        location=LocationItem(name='Dublin-Port,Ireland'),
        local_date_time='01/15/18 15:12',
        vessel=None,
    )



