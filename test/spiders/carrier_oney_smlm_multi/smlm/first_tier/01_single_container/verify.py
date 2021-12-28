from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.oney_smlm_share_spider import (
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
    VesselRoutingRule,
)


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SHSM9C747300',
        final_dest="CHICAGO,IL, UNITED STATES",
        task_id=1,
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    assert results[1].rule_name == VesselRoutingRule.name
    assert results[1].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SHSM9C747300',
    }

    assert results[2] == ContainerItem(
        container_key='CCLU3451951',
        container_no='CCLU3451951',
        task_id=1,
    )

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == ContainerStatusRoutingRule.name
    assert results[3].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CCLU3451951',
        'bkg_no': 'SHSM9C747300',
        'cop_no': 'CSHA9827358813',
    }

    assert isinstance(results[4], RequestOption)
    assert results[4].rule_name == ReleaseStatusRoutingRule.name
    assert results[4].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CCLU3451951',
        'bkg_no': 'SHSM9C747300',
    }

    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == RailInfoRoutingRule.name
    assert results[5].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9827358813',
    }
