import scrapy

from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem


def verify(results):
    assert len(results) == 7

    assert results[0] == MblItem(**{
        'mbl_no': '8021483250',
        'vessel': 'COSCO AMERICA',
        'voyage': '057W',
        'por': LocationItem(**{'name': 'Minneapolis ,Minnesota ,United States'}),
        'pol': LocationItem(**{'name': 'Seattle - SSA Marine T-30'}),
        'pod': LocationItem(**{
            'name': 'Yokohama - Honmoku BC-2 Container Terminal',
            'firms_code': None,
        }),
        'final_dest': LocationItem(**{
            'name': 'Yokohama ,Kanagawa ,Japan',
            'firms_code': None,
        }),
        'etd': '2019-04-30 18:00',
        'atd': '2019-05-01 16:33',
        'eta': '2019-05-26 02:00',
        'ata': '2019-05-26 00:48',
        'bl_type': 'Sea WayBill',
        'deliv_eta': '2019-05-26 09:00',
        'cargo_cutoff_date': '2019-04-19 17:00',
        'surrendered_status': 'Sea Waybill',
    })

    assert results[1] == VesselItem(**{
        'vessel_key': 'COSCO AMERICA',
        'vessel': 'COSCO AMERICA',
        'voyage': '057W',
        'pol': LocationItem(**{'name': 'Seattle'}),
        'pod': LocationItem(**{'name': 'Shanghai'}),
        'etd': '2019-04-30 18:00',
        'atd': '2019-05-01 16:33',
        'eta': '2019-05-19 00:01',
        'ata': '2019-05-19 02:24',
        'discharge_date': '2019-05-19 11:00',
        'shipping_date': '2019-05-01 09:40',
        'row_no': '1',
        'sequence_no': '1',
    })

    assert results[2] == VesselItem(**{
        'vessel_key': 'HYPERION',
        'vessel': 'HYPERION',
        'voyage': '065E',
        'pol': LocationItem(**{'name': 'Shanghai'}),
        'pod': LocationItem(**{'name': 'Yokohama'}),
        'etd': '2019-05-22 02:00',
        'atd': '2019-05-22 13:10',
        'eta': '2019-05-26 02:00',
        'ata': '2019-05-26 00:48',
        'discharge_date': '2019-05-26 01:00',
        'shipping_date': '2019-05-22 13:00',
        'row_no': '2',
        'sequence_no': '3',
    })

    assert results[3] == ContainerItem(**{
        'container_key': 'CSLU173798',
        'last_free_day': None,
        'empty_pickup_date': '2019-04-16 12:04',
        'empty_return_date': '2019-06-12 13:55',
        'full_pickup_date': '2019-06-07 13:59',
        'full_return_date': '2019-04-17 13:11',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    assert results[4] == ContainerItem(**{
        'container_key': 'CSLU235641',
        'last_free_day': None,
        'empty_pickup_date': '2019-04-16 13:16',
        'empty_return_date': '2019-06-10 09:44',
        'full_pickup_date': '2019-06-07 13:49',
        'full_return_date': '2019-04-17 14:11',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    assert results[5] == ContainerItem(**{
        'container_key': 'SEGU149945',
        'last_free_day': None,
        'empty_pickup_date': '2019-04-17 14:41',
        'empty_return_date': '2019-06-10 08:56',
        'full_pickup_date': '2019-06-07 15:26',
        'full_return_date': '2019-04-18 12:48',
        'ams_release': 'Clear',
        'depot_last_free_day': None,
    })

    assert isinstance(results[6], scrapy.Request)
