from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_oney_smlm import (
    VesselRoutingRule, ReleaseStatusRoutingRule, ContainerStatusRoutingRule, RailInfoRoutingRule
)


def verify(results):
    assert results[0] == MblItem(mbl_no='SHFA9A128100')

    assert isinstance(results[1], RequestOption)
    assert results[1].url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    assert results[1].rule_name == VesselRoutingRule.name
    assert results[1].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SHFA9A128100',
    }

    assert results[2] == ContainerItem(
        container_key='FCIU2480151',
        container_no='FCIU2480151',
    )

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == ContainerStatusRoutingRule.name
    assert results[3].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403939',
    }

    assert isinstance(results[4], RequestOption)
    assert results[4].rule_name == ReleaseStatusRoutingRule.name
    assert results[4].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
    }

    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == RailInfoRoutingRule.name
    assert results[5].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403939',
    }

    assert results[14] == ContainerItem(
        container_key='CAIU6468881',
        container_no='CAIU6468881',
    )

    assert isinstance(results[15], RequestOption)
    assert results[15].rule_name == ContainerStatusRoutingRule.name
    assert results[15].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403940',
    }

    assert isinstance(results[16], RequestOption)
    assert results[16].rule_name == ReleaseStatusRoutingRule.name
    assert results[16].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
    }

    assert isinstance(results[17], RequestOption)
    assert results[17].rule_name == RailInfoRoutingRule.name
    assert results[17].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403940',
    }

