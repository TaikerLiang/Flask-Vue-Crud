from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == ContainerStatusItem(**{
            'container_no': 'TRHU2558351',
            'description': 'Discharged at T/S POD',
            'local_date_time': '2019-07-21 07:11',
            'location': LocationItem(**{'name': "Ningbo Beilun Int'l Container Co.,Ningbo,Zhejiang,China"}),
            'transport': '',
            'container_key': '1',
        })

        assert results[1] == ContainerStatusItem(**{
            'container_no': 'TRHU2558351',
            'description': 'Loaded at First POL',
            'local_date_time': '2019-06-28 16:23',
            'location': LocationItem(**{'name': "Long Beach Container Terminal , LLC,Long Beach,California,United States"}),
            'transport': 'Vessel',
            'container_key': '1',
        })

        assert results[2] == ContainerStatusItem(**{
            'container_no': 'TRHU2558351',
            'description': 'Cargo Received',
            'local_date_time': '2019-06-17 09:22',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Truck',
            'container_key': '1',
        })

        assert results[3] == ContainerStatusItem(**{
            'container_no': 'TRHU2558351',
            'description': 'Gate-In at First POL',
            'local_date_time': '2019-06-17 09:22',
            'location': LocationItem(**{'name': 'Long Beach Container Terminal , LLC,Long Beach,California,United States'}),
            'transport': 'Truck',
            'container_key': '1',
        })

        assert results[4] == ContainerStatusItem(**{
            'container_no': 'TRHU2558351',
            'description': 'Empty Equipment Despatched',
            'local_date_time': '2019-06-13 19:00',
            'location': LocationItem(**{'name': 'Pacific Container Terminal,Long Beach,California,United States'}),
            'transport': 'Truck',
            'container_key': '1',
        })
