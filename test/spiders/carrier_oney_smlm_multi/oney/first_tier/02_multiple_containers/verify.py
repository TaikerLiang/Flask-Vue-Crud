from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    VesselRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
)


def verify(results):
    assert results[0] == MblItem(mbl_no='SZPVF2740514', task_id=1, final_dest="PUSAN, KOREA REPUBLIC OF")

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == VesselRoutingRule.name
    assert results[1].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SZPVF2740514',
    }

    assert results[2] == ContainerItem(
        container_key='UETU5848871',
        container_no='UETU5848871',
        task_id=1,
    )

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == ContainerStatusRoutingRule.name
    assert results[3].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848871',
        'bkg_no': 'SZPVF2740514',
        'cop_no': 'CSZP9916113071',
    }

    assert isinstance(results[4], RequestOption)
    assert results[4].rule_name == ReleaseStatusRoutingRule.name
    assert results[4].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848871',
        'bkg_no': 'SZPVF2740514',
    }

    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == RailInfoRoutingRule.name
    assert results[5].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSZP9916113071',
    }

    assert results[18] == ContainerItem(
        container_key='UETU5848906',
        container_no='UETU5848906',
        task_id=1,
    )

    assert isinstance(results[19], RequestOption)
    assert results[19].rule_name == ContainerStatusRoutingRule.name
    assert results[19].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848906',
        'bkg_no': 'SZPVF2740514',
        'cop_no': 'CSZP9916113073',
    }

    assert isinstance(results[20], RequestOption)
    assert results[20].rule_name == ReleaseStatusRoutingRule.name
    assert results[20].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848906',
        'bkg_no': 'SZPVF2740514',
    }

    assert isinstance(results[21], RequestOption)
    assert results[21].rule_name == RailInfoRoutingRule.name
    assert results[21].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSZP9916113073',
    }
