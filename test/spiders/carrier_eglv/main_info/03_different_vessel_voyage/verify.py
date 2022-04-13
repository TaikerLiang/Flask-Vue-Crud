from crawler.core_carrier.items_new import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.spiders.carrier_eglv import ContainerStatusRoutingRule


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no="142901393381",
            vessel=None,
            voyage=None,
            por=LocationItem(name="SHANGHAI (CN)"),
            pol=LocationItem(name="SHANGHAI (CN)"),
            pod=LocationItem(name="LONG BEACH, CA (US)"),
            place_of_deliv=LocationItem(name="LOS ANGELES, CA (US)"),
            etd="OCT-04-2019",
            final_dest=LocationItem(name=None),
            eta=None,
            cargo_cutoff_date=None,
        )

        assert results[1] == ContainerItem(
            container_key="TRIU8882058",
            container_no="TRIU8882058",
        )

        assert isinstance(results[2], RequestOption)
        assert results[2].rule_name == ContainerStatusRoutingRule.name
        assert results[2].meta == {
            "container_no": "TRIU8882058",
        }
