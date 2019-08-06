from crawler.core_carrier.items import MblItem, VesselItem, LocationItem, ContainerItem


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert len(results) == 9

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
            'container_no': 'CSLU1737989',
            'last_free_day': None,
            'empty_pickup_date': '2019-04-16 12:04',
            'empty_return_date': '2019-06-12 13:55',
            'full_pickup_date': '2019-06-07 13:59',
            'full_return_date': '2019-04-17 13:11',
            'ams_release': 'Clear',
            'depot_last_free_day': None,
        })

        assert results[5] == ContainerItem(**{
            'container_no': 'CSLU2356415',
            'last_free_day': None,
            'empty_pickup_date': '2019-04-16 13:16',
            'empty_return_date': '2019-06-10 09:44',
            'full_pickup_date': '2019-06-07 13:49',
            'full_return_date': '2019-04-17 14:11',
            'ams_release': 'Clear',
            'depot_last_free_day': None,
        })

        assert results[7] == ContainerItem(**{
            'container_no': 'SEGU1499450',
            'last_free_day': None,
            'empty_pickup_date': '2019-04-17 14:41',
            'empty_return_date': '2019-06-10 08:56',
            'full_pickup_date': '2019-06-07 15:26',
            'full_return_date': '2019-04-18 12:48',
            'ams_release': 'Clear',
            'depot_last_free_day': None,
        })
        #
        # assert isinstance(results[6], Request)
        # assert isinstance(results[7], Request)
        # assert isinstance(results[8], Request)

        pass



        # assert results[3] == ContainerItem(**{
        #     'container_no': '',
        #     'description': {
        #         ''
        #     },
        #     'timestamp': '',
        #     'location': ''
        # })

        # verify requests
        # assert isinstance(results[3], Request)


# def check_mbl_item(item1, item2):
#     assert isinstance(item1, MblItem)
#     for k, v in item1.items():
#         assert item2[k] == v
#
#
# def check_vessel_item(item1, item2):
#     # assert isinstance(item1, VesselItem)
#     a = item1
#     b = item2
#     assert a == b
#     # for k, v in item1.items():
#     #     assert item2[k] == v
#
#
# def check_container_item(item1, item2):
#     assert isinstance(item1, ContainerItem)
#     for k, v in item1.items():
#         assert item2[k] == v


# def draw_item(results: list, item) -> list:
#     return_list = []
#     for result in results:
#         if isinstance(result, item):
#             return_list.append(result)
#     return return_list


# """
# <class 'dict'>:
# {
#     'mbl_no': '6085396930', 'vessel': 'OOCL HO CHI MINH CITY', 'voyage': '033E', 'por': {'name': 'Kaohsiung ,Taiwan'}, 'pol': {'name': 'Kaohsiung - OOCL (Taiwan) Co., Ltd.'}, 'pod': {'name': 'Long Beach - Long Beach Container Terminal , LLC'}, 'final_dest': {'name': 'Los Angeles ,California ,United States - Long Beach Container '
#          'Terminal , LLC'}, 'etd': '2019-05-09 02:00', 'atd': '2019-05-09 00:26', 'eta': '2019-05-22 08:00', 'ata': '2019-05-22 06:06',
# }
# """
