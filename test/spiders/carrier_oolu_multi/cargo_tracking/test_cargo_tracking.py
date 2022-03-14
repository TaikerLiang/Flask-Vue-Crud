# from pathlib import Path

# import pytest
# from scrapy import Request
# from scrapy.http import TextResponse

# from crawler.core_carrier.base_new import SHIPMENT_TYPE_MBL
# from crawler.spiders.carrier_oolu_multi import CargoTrackingRule, ContentGetter, _PageLocator
# from test.spiders.carrier_oolu_multi import cargo_tracking


# @pytest.fixture
# def sample_loader(sample_loader):
#     sample_path = Path(__file__).parent
#     sample_loader.setup(sample_package=cargo_tracking, sample_path=sample_path)
#     return sample_loader


# @pytest.mark.parametrize(
#     "sub,mbl_no",
#     [
#         ("01_single_container", "2625845270"),
#         ("02_multi_containers", "2109051600"),
#         ("03_without_custom_release_date", "2628633440"),
#         ("04_tranship_exist", "2630699272"),
#         ("05_custom_release_title_exist_but_value_empty", "2635541720"),
#         ("06_detail_table_not_exist", "2650422090"),
#     ],
# )
# def test_cargo_tracking_handler(sub, mbl_no, sample_loader):
#     html_file = sample_loader.read_file(sub, "sample.html")

#     option = CargoTrackingRule.build_request_option(search_nos=mbl_no, task_ids="1")
#     response = TextResponse(
#         url=option.url,
#         body=html_file,
#         encoding="utf-8",
#         request=Request(
#             url=option.url,
#             meta=option.meta,
#         ),
#     )
#     locator = _PageLocator()
#     selector_map = locator.locate_selectors(response=response)
#     results = [CargoTrackingRule._extract_custom_release_info(selector_map),
#                CargoTrackingRule._extract_routing_info(selector_map)]

#     verify_module = sample_loader.load_sample_module(sub, "verify")
#     verify_module.verify(results=results)


# @pytest.mark.parametrize(
#     "sub,mbl_no",
#     [
#         ("07_invalid_mbl_no", "OOLU0000000000"),
#     ],
# )
# def test_is_search_no_invalid(sub, mbl_no, sample_loader):
#     html_file = sample_loader.read_file(sub, "sample.html")

#     option = CargoTrackingRule.build_request_option(search_nos=mbl_no, task_ids="1")
#     response = TextResponse(
#         url=option.url,
#         body=html_file,
#         encoding="utf-8",
#         request=Request(
#             url=option.url,
#             meta=option.meta,
#         ),
#     )

#     results = [CargoTrackingRule.is_search_no_invalid(response=response)]

#     verify_module = sample_loader.load_sample_module(sub, "verify")
#     verify_module.verify(results=results)
