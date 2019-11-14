from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):

    assert results[0] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Loaded at T/S POL',
        'local_date_time': '2019-07-16 02:00',
        'location': LocationItem(**{'name': 'Sha Port Ctn Waigaoqiao Phase V Tml,Shanghai,Shanghai,China'}),
        'transport': 'Vessel',
    })

    assert results[1] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Discharged at T/S POD',
        'local_date_time': '2019-07-13 20:00',
        'location': LocationItem(**{'name': 'Shanghai Shengdong (I), Yangshan,Shanghai,Shanghai,China'}),
        'transport': '',
    })

    assert results[2] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Loaded at First POL',
        'local_date_time': '2019-06-27 12:57',
        'location': LocationItem(**{'name': 'DP World-Centerm Container Terminal,Vancouver,British Columbia,Canada'}),
        'transport': 'Vessel',
    })

    assert results[3] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Gate-In at First POL',
        'local_date_time': '2019-06-21 09:37',
        'location': LocationItem(**{'name': 'DP World-Centerm Container Terminal,Vancouver,British Columbia,Canada'}),
        'transport': 'Rail',
    })

    assert results[4] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'First Rail Departure under O/B',
        'local_date_time': '2019-06-13 17:27',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Rail',
    })

    assert results[5] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Gate-out from First Full Facility',
        'local_date_time': '2019-06-13 17:27',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Rail',
    })

    assert results[6] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Rail Departure at POR',
        'local_date_time': '2019-06-13 17:27',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Rail',
    })

    assert results[7] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'First Loaded on Rail under O/B',
        'local_date_time': '2019-06-13 10:50',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Rail',
    })

    assert results[8] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Loaded on Rail at POR',
        'local_date_time': '2019-06-13 10:50',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Rail',
    })

    assert results[9] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Cargo Received',
        'local_date_time': '2019-06-11 07:36',
        'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
        'transport': 'Truck',
    })

    assert results[10] == ContainerStatusItem(**{
        'container_key': '1',
        'description': 'Empty Equipment Despatched',
        'local_date_time': '2019-06-06 08:29',
        'location': LocationItem(**{'name': 'M&N Equipment Services,Minneapolis,Minnesota,United States'}),
        'transport': 'Truck',
    })
