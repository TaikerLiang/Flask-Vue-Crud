from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key='ZCSU2764374',
        description='Empty container dispatched from inland point to Customer',
        location=LocationItem(name="Ningbo , China. People's Republic"),
        local_date_time='21-Sep-2019',
    )

    assert results[3] == ContainerStatusItem(
        container_key='ZCSU2764374',
        description='Carrier Release',
        location=LocationItem(name="Laem Chabang, Thailand"),
        local_date_time='04-Oct-2019',
    )

    assert results[5] == ContainerStatusItem(
        container_key='ZCSU2764374',
        description='Container was discharged at Port of Destination',
        location=LocationItem(name="Laem Chabang, Thailand"),
        local_date_time='06-Oct-2019',
    )

    assert results[9] == ContainerStatusItem(
        container_key='ZCSU2764374',
        description='Empty container returned from Customer',
        location=LocationItem(name="Laem Chabang, Thailand"),
        local_date_time='08-Oct-2019',
    )
