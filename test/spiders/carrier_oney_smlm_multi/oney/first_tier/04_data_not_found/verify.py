from crawler.core.base_new import RESULT_STATUS_ERROR, SEARCH_TYPE_MBL
from crawler.core.items_new import DataNotFoundItem
from crawler.core_carrier.items_new import ContainerItem, MblItem
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    NextRoundRoutingRule,
    VesselRoutingRule,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.spiders.carrier_oney_multi import CarrierOneySpider


def verify(results):
    assert results[0] == MblItem(
        mbl_no="RICBDW223900", task_id=1, final_dest={"name": "LOS ANGELES, CA, UNITED STATES"}
    )

    # results[1] is an EndItem
    assert isinstance(results[2], RequestOption)
    assert results[2].rule_name == VesselRoutingRule.name
    assert results[2].form_data == {
        "f_cmd": VesselRoutingRule.f_cmd,
        "bkg_no": "RICBDW223900",
    }

    assert results[3] == MblItem(mbl_no="RICBDK658400", task_id=2, final_dest={"name": "SHANGHAI, SHANGHAI, CHINA"})

    # results[4] is an EndItem
    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == VesselRoutingRule.name
    assert results[5].form_data == {
        "f_cmd": VesselRoutingRule.f_cmd,
        "bkg_no": "RICBDK658400",
    }

    assert results[6] == DataNotFoundItem(
        search_no="DALA35925000",
        search_type=SEARCH_TYPE_MBL,
        status=RESULT_STATUS_ERROR,
        detail="Data was not found",
        task_id=3,
    )
    assert results[7] == ContainerItem(
        container_key="NYKU3438324",
        container_no="NYKU3438324",
        task_id=2,
    )

    assert isinstance(results[52], RequestOption)
    assert results[52].rule_name == NextRoundRoutingRule.name
    assert results[52].url == "https://eval.edi.hardcoretech.co/c/livez"
    assert results[52].meta == {
        "search_nos": ["RICBDW223900", "RICBDK658400", "DALA35925000"],
        "task_ids": [1, 2, 3],
        "base_url": CarrierOneySpider.base_url,
    }
