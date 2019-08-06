from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Loaded at T/S POL',
            'timestamp': '2019-07-16 02:00',
            'location': LocationItem(**{'name': 'Sha Port Ctn Waigaoqiao Phase V Tml,Shanghai,Shanghai,China'}),
            'transport': 'Vessel',
        })

        assert results[1] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Discharged at T/S POD',
            'timestamp': '2019-07-13 20:00',
            'location': LocationItem(**{'name': 'Shanghai Shengdong (I), Yangshan,Shanghai,Shanghai,China'}),
            'transport': ' ',
        })

        assert results[2] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Loaded at First POL',
            'timestamp': '2019-06-27 12:57',
            'location': LocationItem(**{'name': 'DP World-Centerm Container Terminal,Vancouver,British Columbia,Canada'}),
            'transport': 'Vessel'
        })

        assert results[3] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Gate-In at First POL',
            'timestamp': '2019-06-21 09:37',
            'location': LocationItem(**{'name': 'DP World-Centerm Container Terminal,Vancouver,British Columbia,Canada'}),
            'transport': 'Rail',
        })

        assert results[4] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'First Rail Departure under O/B',
            'timestamp': '2019-06-13 17:27',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Rail',
        })

        assert results[5] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Gate-out from First Full Facility',
            'timestamp': '2019-06-13 17:27',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Rail',
        })

        assert results[6] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Rail Departure at POR',
            'timestamp': '2019-06-13 17:27',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Rail',
        })

        assert results[7] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'First Loaded on Rail under O/B',
            'timestamp': '2019-06-13 10:50',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Rail',
        })

        assert results[8] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Loaded on Rail at POR',
            'timestamp': '2019-06-13 10:50',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Rail',
        })

        assert results[9] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Cargo Received',
            'timestamp': '2019-06-11 07:36',
            'location': LocationItem(**{'name': 'CP (Minneapolis),Minneapolis,Minnesota,United States'}),
            'transport': 'Truck'

        })

        assert results[10] == ContainerStatusItem(**{
            'container_no': 'FCIU5635365',
            'description': 'Empty Equipment Despatched',
            'timestamp': '2019-06-06 08:29',
            'location': LocationItem(**{'name': 'M&N Equipment Services,Minneapolis,Minnesota,United States'}),
            'transport': 'Truck',
        })

