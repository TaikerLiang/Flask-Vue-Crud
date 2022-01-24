from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_aclu import DetailTrackingRoutingRule


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == DetailTrackingRoutingRule.name
    assert (
        results[0].url
        == "https://myacl.aclcargo.com/trackCargo.php?EquiPk=11779178450&ShipFk=17769882100&EmoFk=0&acl_track=ACLU9700046&Equino=ACLU9700046&verbosity=detail"
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DetailTrackingRoutingRule.name
    assert (
        results[1].url
        == "https://myacl.aclcargo.com/trackCargo.php?EquiPk=11739028889&ShipFk=17769882100&EmoFk=0&acl_track=ACLU9685173&Equino=ACLU9685173&verbosity=detail"
    )
