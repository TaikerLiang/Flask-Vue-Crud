from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_aclu import DetailTrackingRoutingRule


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == DetailTrackingRoutingRule.name
    assert results[0].form_data == {
        "EmoFk": "0",
        "EquiPk": "11779178450",
        "Equino": "ACLU9700046",
        "ShipFk": "17769882100",
        "acl_track": "ACLU9700046",
        "request": "SA-00715282",
        "verbosity": "detail",
    }

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DetailTrackingRoutingRule.name
    assert results[1].form_data == {
        "EmoFk": "0",
        "EquiPk": "11739028889",
        "Equino": "ACLU9685173",
        "ShipFk": "17769882100",
        "acl_track": "ACLU9685173",
        "request": "SA-00715282",
        "verbosity": "detail",
    }
