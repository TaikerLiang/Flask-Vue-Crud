import scrapy

from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem


def verify(results):
    assert len(results) == 5

    assert results[0] == MblItem(**{
        'mbl_no': '6085396930',
        'vessel': 'OOCL HO CHI MINH CITY',
        'voyage': '033E',
        'por': LocationItem(**{'name': 'Kaohsiung ,Taiwan'}),
        'pol': LocationItem(**{'name': 'Kaohsiung - OOCL (Taiwan) Co., Ltd.'}),
        'pod': LocationItem(**{
            'name': 'Long Beach - Long Beach Container Terminal , LLC',
            'firms_code': None,
        }),
        'final_dest': LocationItem(**{
            'name': 'Los Angeles ,California ,United States',
            'firms_code': None,
        }),
        'etd': '2019-05-09 02:00',
        'atd': '2019-05-09 00:26',
        'eta': '2019-05-22 08:00',
        'ata': '2019-05-22 06:06',
        'bl_type': 'Sea WayBill',
        'deliv_eta': '2019-05-23 22:00',
        'cargo_cutoff_date': '2019-05-06 16:00',
        'surrendered_status': 'Sea Waybill',
    })

    assert results[1] == VesselItem(**{
        'vessel_key': 'OOCL HO CHI MINH CITY',
        'vessel': 'OOCL HO CHI MINH CITY',
        'voyage': '033E',
        'pol': LocationItem(**{'name': 'Kaohsiung'}),
        'pod': LocationItem(**{'name': 'Long Beach'}),
        'etd': '2019-05-09 02:00',
        'atd': '2019-05-09 00:26',
        'eta': '2019-05-22 08:00',
        'ata': '2019-05-22 06:06',
        'discharge_date': '2019-05-22 13:53',
        'shipping_date': '2019-05-08 21:06',
        'row_no': '1',
        'sequence_no': '1'
    })

    assert results[2] == ContainerItem(**{
        'container_key': '1',
        'last_free_day': '2019-05-29',
        'empty_pickup_date': '2019-04-29 10:36',
        'empty_return_date': '2019-05-31 08:43',
        'full_pickup_date': '2019-05-28 14:57',
        'full_return_date': '2019-05-02 12:48',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    assert results[3] == ContainerItem(**{
        'container_key': '2',
        'last_free_day': '2019-05-29',
        'empty_pickup_date': '2019-04-30 13:54',
        'empty_return_date': '2019-05-30 12:09',
        'full_pickup_date': '2019-05-28 15:52',
        'full_return_date': '2019-05-02 20:12',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    # verify requests
    assert isinstance(results[4], scrapy.Request)
