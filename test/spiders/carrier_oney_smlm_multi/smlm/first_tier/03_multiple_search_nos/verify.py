from crawler.core.base_new import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.description import DATA_NOT_FOUND_DESC
from crawler.core.items_new import DataNotFoundItem
from crawler.core_carrier.oney_smlm_multi_share_spider import NextRoundRoutingRule
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.spiders.carrier_smlm_multi import CarrierSmlmSpider


def verify(results):
    assert results[0] == DataNotFoundItem(
        search_no="SHSB1FY71701",
        search_type=SEARCH_TYPE_MBL,
        status=RESULT_STATUS_ERROR,
        detail=DATA_NOT_FOUND_DESC,
        task_id=1,
    )

    assert isinstance(results[24], RequestOption)
    assert results[24].url == "https://eval.edi.hardcoretech.co/c/livez"
    assert results[24].rule_name == NextRoundRoutingRule.name
    assert results[24].meta == {
        "search_nos": ["SHSB1FY71701", "NJBH1A243500"],
        "task_ids": [1, 2],
        "base_url": CarrierSmlmSpider.base_url,
    }
