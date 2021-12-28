from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    VesselRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
)


def verify(results):
    assert results[0] == MblItem(mbl_no='RICBDW223900', task_id=1, final_dest="LOS ANGELES, CA, UNITED STATES")

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == VesselRoutingRule.name
    assert results[1].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'RICBDW223900',
    }

    assert results[2] == MblItem(mbl_no='RICBDK658400', task_id=2, final_dest="SHANGHAI, SHANGHAI, CHINA")

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == VesselRoutingRule.name
    assert results[3].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'RICBDK658400',
    }

    assert results[4] == MblItem(mbl_no='RICBAR817500', task_id=3, final_dest="LOS ANGELES, CA, UNITED STATES")

    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == VesselRoutingRule.name
    assert results[5].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'RICBAR817500',
    }

    assert results[6] == ContainerItem(
        container_key='TCLU8945254',
        container_no='TCLU8945254',
        task_id=3,
    )

    assert isinstance(results[7], RequestOption)
    assert results[7].rule_name == ContainerStatusRoutingRule.name
    assert results[7].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU8945254',
        'bkg_no': 'RICBAR817500',
        'cop_no': 'CRIC1716538560',
    }

    assert isinstance(results[8], RequestOption)
    assert results[8].rule_name == ReleaseStatusRoutingRule.name
    assert results[8].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU8945254',
        'bkg_no': 'RICBAR817500',
    }

    assert isinstance(results[9], RequestOption)
    assert results[9].rule_name == RailInfoRoutingRule.name
    assert results[9].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CRIC1716538560',
    }

    assert results[42] == ContainerItem(
        container_key='TCLU3191927',
        container_no='TCLU3191927',
        task_id=1,
    )

    assert isinstance(results[43], RequestOption)
    assert results[43].rule_name == ContainerStatusRoutingRule.name
    assert results[43].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU3191927',
        'bkg_no': 'RICBDW223900',
        'cop_no': 'CRIC1608275197',
    }

    assert isinstance(results[44], RequestOption)
    assert results[44].rule_name == ReleaseStatusRoutingRule.name
    assert results[44].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU3191927',
        'bkg_no': 'RICBDW223900',
    }

    assert isinstance(results[45], RequestOption)
    assert results[45].rule_name == RailInfoRoutingRule.name
    assert results[45].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CRIC1608275197',
    }
