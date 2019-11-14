from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem


def verify(results):
    assert results[0] == MblItem(**{
        'mbl_no': '6216853000',
        'vessel': 'KOTA PERDANA',
        'voyage': 'E011',
        'por': LocationItem(**{'name': 'Shanghai ,China'}),
        'pol': LocationItem(**{'name': 'Shanghai - ShanghaiPort Ctn Waigaoqiao Tml Brh'}),
        'pod': LocationItem(**{
            'name': 'Long Beach - Pacific Container Terminal',
            'firms_code': 'W182',
        }),
        'final_dest': LocationItem(**{
            'name': 'Long Beach ,California ,United States',
            'firms_code': 'W182',
        }),
        'etd': '2019-08-05 15:30',
        'atd': None,
        'eta': '2019-08-19 16:00',
        'ata': None,
        'deliv_eta': '2019-08-20 18:00',
        'cargo_cutoff_date': "2019-07-31 00:00",
        'surrendered_status': None,
        'container_quantity': '40HQ*1',
        'trans_eta': '2019-08-19 16:00',
    })

    assert results[1] == VesselItem(**{
        'vessel_key': 'KOTA PERDANA',
        'vessel': 'KOTA PERDANA',
        'voyage': 'E011',
        'pol': LocationItem(**{'name': 'Shanghai'}),
        'pod': LocationItem(**{'name': 'Long Beach'}),
        'etd': '2019-08-05 15:30',
        'atd': None,
        'eta': '2019-08-19 16:00',
        'ata': None,
        'discharge_date': None,
        'shipping_date': None,
        'row_no': '1',
        'sequence_no': '1',
    })

    assert results[2] == ContainerItem(**{
        'container_key': 'CSNU629304',
        'last_free_day': None,
        'empty_pickup_date': '2019-07-30 17:01',
        'empty_return_date': None,
        'full_pickup_date': None,
        'full_return_date': '2019-07-31 20:09',
        'ams_release': 'Not Clear',
        'depot_last_free_day': None,
    })
