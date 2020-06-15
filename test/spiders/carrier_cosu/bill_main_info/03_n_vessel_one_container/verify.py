from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results):
    assert results[0] == MblItem(**{
        'mbl_no': '8021543080',
        'vessel': 'XIN BEIJING',
        'voyage': '109S',
        'por': LocationItem(**{'name': 'Minneapolis ,Minnesota ,United States'}),
        'pol': LocationItem(**{'name': 'Vancouver - DP World-Centerm Container Terminal'}),
        'pod': LocationItem(**{
            'name': 'Yokohama - Honmoku BC-2 Container Terminal',
            'firms_code': None,
        }),
        'final_dest': LocationItem(**{
            'name': 'Yokohama ,Kanagawa ,Japan',
            'firms_code': None,
        }),
        'etd': '2019-06-29 01:00',
        'atd': '2019-06-29 18:10',
        'eta': '2019-07-19 13:00',
        'ata': None,
        'bl_type': 'Sea WayBill',
        'deliv_eta': '2019-07-20 09:00',
        'cargo_cutoff_date': None,
        'surrendered_status': 'Sea Waybill',
    })

    assert results[1] == VesselItem(**{
        'vessel_key': 'XIN BEIJING',
        'vessel': 'XIN BEIJING',
        'voyage': '109S',
        'pol': LocationItem(**{'name': 'Vancouver'}),
        'pod': LocationItem(**{'name': 'Shanghai'}),
        'etd': '2019-06-29 01:00',
        'atd': '2019-06-29 18:10',
        'eta': '2019-07-12 14:00',
        'ata': '2019-07-12 22:26',
        'discharge_date': '2019-07-13 20:00',
        'shipping_date': '2019-06-27 12:57',
        'row_no': '1',
        'sequence_no': '1',
    })

    assert results[2] == VesselItem(**{
        'vessel_key': 'MARCLOUD',
        'vessel': 'MARCLOUD',
        'voyage': '253E',
        'pol': LocationItem(**{'name': 'Shanghai'}),
        'pod': LocationItem(**{'name': 'Yokohama'}),
        'etd': '2019-07-16 02:00',
        'atd': '2019-07-16 02:12',
        'eta': '2019-07-19 13:00',
        'ata': None,
        'discharge_date': None,
        'shipping_date': '2019-07-16 02:00',
        'row_no': '2',
        'sequence_no': '3',
    })

    assert results[3] == ContainerItem(**{
        'container_key': 'FCIU563536',
        'last_free_day': None,
        'empty_pickup_date': '2019-06-06 08:29',
        'empty_return_date': None,
        'full_pickup_date': None,
        'full_return_date': '2019-06-11 07:36',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    # verify requests
    assert isinstance(results[4], RequestOption)

