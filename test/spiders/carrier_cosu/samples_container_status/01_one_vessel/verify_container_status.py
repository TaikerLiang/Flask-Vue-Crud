from crawler.core_carrier.items import ContainerStatusItem, LocationItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):

        assert results[0] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Empty Equipment Returned',
            'local_date_time': '2019-06-06 13:14',
            'location': LocationItem(**{'name': 'Pacific Container Terminal,Long Beach,California,United States'}),
            'transport': 'Truck',
        })

        assert results[1] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Gate-out from Final Hub',
            'local_date_time': '2019-06-05 08:34',
            'location': LocationItem(**{'name': 'American President Line,Los Angeles,California,United States'}),
            'transport': 'Truck',
        })

        assert results[2] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Discharged at Last POD',
            'local_date_time': '2019-06-01 15:19',
            'location': LocationItem(**{'name': 'American President Line,Los Angeles,California,United States'}),
            'transport': '',
        })

        assert results[3] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Loaded at First POL',
            'local_date_time': '2019-05-07 23:00',
            'location': LocationItem(**{'name': 'JICT.1 (UTC-1),Jakarta,Jakarta Raya,Indonesia'}),
            'transport': 'Vessel',
        })

        assert results[4] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Cargo Received',
            'local_date_time': '2019-05-04 21:46',
            'location': LocationItem(**{'name': 'JICT.1 (UTC-1),Jakarta,Jakarta Raya,Indonesia'}),
            'transport': 'Truck',
        })

        assert results[5] == ContainerStatusItem(**{
            'container_key': '1',
            'container_no': 'CSNU6276212',
            'description': 'Gate-In at First POL',
            'local_date_time': '2019-05-04 21:46',
            'location': LocationItem(**{'name': 'JICT.1 (UTC-1),Jakarta,Jakarta Raya,Indonesia'}),
            'transport': 'Truck',
        })
