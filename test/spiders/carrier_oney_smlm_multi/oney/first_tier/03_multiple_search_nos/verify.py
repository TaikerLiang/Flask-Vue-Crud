from crawler.core_carrier.items_new import ContainerItem, MblItem
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
    ReleaseStatusRoutingRule,
    VesselRoutingRule,
)
from crawler.core_carrier.request_helpers_new import RequestOption


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

    assert results[6] == MblItem(
        mbl_no="RICBAR817500", task_id=3, final_dest={"name": "LOS ANGELES, CA, UNITED STATES"}
    )

    # results[7] is an EndItem
    assert isinstance(results[8], RequestOption)
    assert results[8].rule_name == VesselRoutingRule.name
    assert results[8].form_data == {
        "f_cmd": VesselRoutingRule.f_cmd,
        "bkg_no": "RICBAR817500",
    }

    assert results[9] == ContainerItem(
        container_key="TCLU8945254",
        container_no="TCLU8945254",
        task_id=3,
    )

    # results[10] is an EndItem
    assert isinstance(results[11], RequestOption)
    assert results[11].rule_name == ContainerStatusRoutingRule.name
    assert results[11].form_data == {
        "f_cmd": ContainerStatusRoutingRule.f_cmd,
        "cntr_no": "TCLU8945254",
        "bkg_no": "RICBAR817500",
        "cop_no": "CRIC1716538560",
    }

    assert isinstance(results[12], RequestOption)
    assert results[12].rule_name == ReleaseStatusRoutingRule.name
    assert results[12].form_data == {
        "f_cmd": ReleaseStatusRoutingRule.f_cmd,
        "cntr_no": "TCLU8945254",
        "bkg_no": "RICBAR817500",
    }

    assert isinstance(results[13], RequestOption)
    assert results[13].rule_name == RailInfoRoutingRule.name
    assert results[13].form_data == {
        "f_cmd": RailInfoRoutingRule.f_cmd,
        "cop_no": "CRIC1716538560",
    }

    assert results[44] == ContainerItem(
        container_key="NYKU3438324",
        container_no="NYKU3438324",
        task_id=2,
    )

    # results[45] is an EndItem
    assert isinstance(results[46], RequestOption)
    assert results[46].rule_name == ContainerStatusRoutingRule.name
    assert results[46].form_data == {
        "f_cmd": ContainerStatusRoutingRule.f_cmd,
        "cntr_no": "NYKU3438324",
        "bkg_no": "RICBDK658400",
        "cop_no": "CRIC1603067489",
    }

    assert isinstance(results[47], RequestOption)
    assert results[47].rule_name == ReleaseStatusRoutingRule.name
    assert results[47].form_data == {
        "f_cmd": ReleaseStatusRoutingRule.f_cmd,
        "cntr_no": "NYKU3438324",
        "bkg_no": "RICBDK658400",
    }

    assert isinstance(results[48], RequestOption)
    assert results[48].rule_name == RailInfoRoutingRule.name
    assert results[48].form_data == {
        "f_cmd": RailInfoRoutingRule.f_cmd,
        "cop_no": "CRIC1603067489",
    }
