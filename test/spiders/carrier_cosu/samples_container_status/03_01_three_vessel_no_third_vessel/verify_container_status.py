from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Loaded at T/S POL',
            'local_date_time': '2019-07-16 08:00',
            'location': LocationItem(**{'name': 'Ningbo Yuandong Terminals Limited,Ningbo,Zhejiang,China'}),
            'transport': 'Vessel',
        })

        assert results[1] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Discharged at T/S POD',
            'local_date_time': '2019-07-11 01:03',
            'location': LocationItem(**{'name': "Ningbo Beilun Int'l Container Co.,Ningbo,Zhejiang,China"}),
            'transport': '',
        })

        assert results[2] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Loaded at First POL',
            'local_date_time': '2019-06-15 18:41',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Vessel',
        })

        assert results[3] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Cargo Received',
            'local_date_time': '2019-06-05 21:45',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Truck',
        })

        assert results[4] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Gate-In at First POL',
            'local_date_time': '2019-06-05 21:45',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Truck',
        })

        assert results[5] == ContainerStatusItem(**{
            'container_no': 'CCLU7463821',
            'description': 'Empty Equipment Despatched',
            'local_date_time': '2019-06-05 15:02',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Truck',
        })
