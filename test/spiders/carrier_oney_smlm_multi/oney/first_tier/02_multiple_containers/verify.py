from crawler.core_carrier.items_new import ContainerItem, MblItem
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
    ReleaseStatusRoutingRule,
    VesselRoutingRule,
)
from crawler.core_carrier.request_helpers_new import RequestOption


def verify(results):
    assert results[0] == MblItem(mbl_no="SZPVF2740514", task_id=1, final_dest={"name": "PUSAN, KOREA REPUBLIC OF"})

    # results[1] is an EndItem
    assert isinstance(results[2], RequestOption)
    assert results[2].rule_name == VesselRoutingRule.name
    assert results[2].form_data == {
        "f_cmd": VesselRoutingRule.f_cmd,
        "bkg_no": "SZPVF2740514",
    }

    assert results[3] == ContainerItem(
        container_key="UETU5848871",
        container_no="UETU5848871",
        task_id=1,
    )

    # results[4] is an EndItem
    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == ContainerStatusRoutingRule.name
    assert results[5].form_data == {
        "f_cmd": ContainerStatusRoutingRule.f_cmd,
        "cntr_no": "UETU5848871",
        "bkg_no": "SZPVF2740514",
        "cop_no": "CSZP9916113071",
    }

    assert isinstance(results[6], RequestOption)
    assert results[6].rule_name == ReleaseStatusRoutingRule.name
    assert results[6].form_data == {
        "f_cmd": ReleaseStatusRoutingRule.f_cmd,
        "cntr_no": "UETU5848871",
        "bkg_no": "SZPVF2740514",
    }

    assert isinstance(results[7], RequestOption)
    assert results[7].rule_name == RailInfoRoutingRule.name
    assert results[7].form_data == {
        "f_cmd": RailInfoRoutingRule.f_cmd,
        "cop_no": "CSZP9916113071",
    }

    assert results[18] == ContainerItem(
        container_key="UETU5847089",
        container_no="UETU5847089",
        task_id=1,
    )

    # results[19] is an EndItem
    assert isinstance(results[20], RequestOption)
    assert results[20].rule_name == ContainerStatusRoutingRule.name
    assert results[20].form_data == {
        "f_cmd": ContainerStatusRoutingRule.f_cmd,
        "cntr_no": "UETU5847089",
        "bkg_no": "SZPVF2740514",
        "cop_no": "CSZP9916113074",
    }

    assert isinstance(results[21], RequestOption)
    assert results[21].rule_name == ReleaseStatusRoutingRule.name
    assert results[21].form_data == {
        "f_cmd": ReleaseStatusRoutingRule.f_cmd,
        "cntr_no": "UETU5847089",
        "bkg_no": "SZPVF2740514",
    }

    assert isinstance(results[22], RequestOption)
    assert results[22].rule_name == RailInfoRoutingRule.name
    assert results[22].form_data == {
        "f_cmd": RailInfoRoutingRule.f_cmd,
        "cop_no": "CSZP9916113074",
    }
