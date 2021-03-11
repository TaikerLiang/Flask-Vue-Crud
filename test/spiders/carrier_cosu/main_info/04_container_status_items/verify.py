from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(items):

    assert items[0] == ContainerStatusItem(**{
        'container_key': 'CSNU639560',
        'description': 'Empty Equipment Despatched',
        'local_date_time': '2020-11-25 14:54',
        'location': LocationItem(**{'name': "Yantian  Int'l  Container Tml,Yantian,Guangdong,China"}),
        'transport': 'Truck',
    })

    assert items[4] == ContainerStatusItem(**{
        'container_key': 'CSNU639560',
        'description': 'Discharged at T/S POD',
        'local_date_time': '2020-12-05 22:36',
        'location': LocationItem(**{'name': 'Shanghai Shengdong (I), Yangshan,Shanghai,Shanghai,China'}),
        'transport': 'Vessel',
    })

    assert items[8] == ContainerStatusItem(**{
        'container_key': 'CSNU639560',
        'description': 'Empty Equipment Returned',
        'local_date_time': '2021-01-12 18:32',
        'location': LocationItem(**{'name': 'West Basin Container Terminal(WBCT),Los Angeles,California,United States'}),
        'transport': 'Truck',
    })

