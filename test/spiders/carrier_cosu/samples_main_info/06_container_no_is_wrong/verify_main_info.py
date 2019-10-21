from scrapy import Request

from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert len(results) == 4

        assert results[0] == MblItem(**{
            'mbl_no': '6205749080',
            'vessel': 'COSCO EUROPE',
            'voyage': '069E',
            'por': LocationItem(**{'name': 'Yantian ,Guangdong ,China'}),
            'pol': LocationItem(**{'name': "Yantian - Yantian  Int'l  Container Tml"}),
            'pod': LocationItem(**{
                'name': 'Long Beach - Pacific Container Terminal',
                'firms_code': 'W182',
            }),
            'final_dest': LocationItem(**{
                'name': 'Long Beach ,California ,United States',
                'firms_code': 'W182',
            }),
            'etd': '2019-08-26 00:00',
            'atd': '2019-08-26 00:38',
            'eta': '2019-09-09 06:00',
            'ata': '2019-09-09 05:28',
            'bl_type': 'Sea WayBill',
            'deliv_eta': '2019-09-10 03:00',
            'cargo_cutoff_date': "2019-08-24 09:00",
            'surrendered_status': 'Sea Waybill',
        })

        assert results[1] == VesselItem(**{
            'vessel_key': 'COSCO EUROPE',
            'vessel': 'COSCO EUROPE',
            'voyage': '069E',
            'ata': '2019-09-09 05:28',
            'atd': '2019-08-26 00:38',
            'discharge_date': '2019-09-11 13:56',
            'eta': '2019-09-09 06:00',
            'etd': '2019-08-26 00:00',
            'pod': {'name': 'Long Beach'},
            'pol': {'name': 'Yantian'},
            'row_no': '1',
            'sequence_no': '1',
            'shipping_date': '2019-08-25 07:54',
        })

        assert results[2] == ContainerItem(**{
            'container_key': '1',
            'ams_release': 'Clear',
            'depot_last_free_day': None,
            'empty_pickup_date': '2019-08-18 02:11',
            'empty_return_date': '2019-09-17 15:00',
            'full_pickup_date': '2019-09-17 00:02',
            'full_return_date': '2019-08-20 06:30',
            'last_free_day': '2019-09-16'
        })

        # verify requests
        # assert isinstance(results[2], Request)
        assert isinstance(results[3], Request)
