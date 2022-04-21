from crawler.core_carrier.items_new import ContainerItem, MblItem
from crawler.core_carrier.oney_smlm_share_spider import (
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
    ReleaseStatusRoutingRule,
    VesselRoutingRule,
)
from crawler.core_carrier.request_helpers_new import RequestOption


def verify(results):
    assert results[0] == MblItem(
        mbl_no="SHSM9C747300",
    )

    # results[1] is an EndItem
    assert isinstance(results[2], RequestOption)
    assert results[2].url == "https://esvc.smlines.com/smline/CUP_HOM_3301GS.do"
    assert results[2].rule_name == VesselRoutingRule.name
    assert results[2].form_data == {
        "f_cmd": VesselRoutingRule.f_cmd,
        "bkg_no": "SHSM9C747300",
    }

    assert results[3] == ContainerItem(
        container_key="CCLU3451951",
        container_no="CCLU3451951",
    )

    # results[4] is an EndItem
    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == ContainerStatusRoutingRule.name
    assert results[5].form_data == {
        "f_cmd": ContainerStatusRoutingRule.f_cmd,
        "cntr_no": "CCLU3451951",
        "bkg_no": "SHSM9C747300",
        "cop_no": "CSHA9827358813",
    }

    assert isinstance(results[6], RequestOption)
    assert results[6].rule_name == ReleaseStatusRoutingRule.name
    assert results[6].form_data == {
        "f_cmd": ReleaseStatusRoutingRule.f_cmd,
        "cntr_no": "CCLU3451951",
        "bkg_no": "SHSM9C747300",
    }

    assert isinstance(results[7], RequestOption)
    assert results[7].rule_name == RailInfoRoutingRule.name
    assert results[7].form_data == {
        "f_cmd": RailInfoRoutingRule.f_cmd,
        "cop_no": "CSHA9827358813",
    }
