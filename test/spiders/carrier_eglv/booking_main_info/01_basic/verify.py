from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_eglv import ContainerStatusRoutingRule, FilingStatusRoutingRule, ReleaseStatusRoutingRule


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            booking_no='456110381786',
            vessel='EVER FAME',
            voyage='1203-003W',
            por=LocationItem(name='OAKLAND, CA (US)'),
            pol=LocationItem(name='OAKLAND, CA (US)'),
            pod=LocationItem(name='TAIPEI (TW)'),
            place_of_deliv=LocationItem(name='KEELUNG (TW)'),
            etd='SEP-10-2021',
            eta='SEP-22-2021',
            cargo_cutoff_date='SEP-01-2021',
            est_onboard_date='SEP-10-2021',
            us_filing_date=None,
            us_filing_status=None,
        )

        assert results[1] == ContainerItem(
            container_key='EITU1980829',
            container_no='EITU1980829',
            full_pickup_date='AUG-24-2021 13:55',
        )

        assert isinstance(results[2], RequestOption)
        assert results[2].rule_name == ContainerStatusRoutingRule.name
        assert results[2].meta == {
            'container_no': 'EITU1980829',
        }
        assert results[2].form_data == {
            'bl_no': '456110381786',
            'cntr_no': 'EITU1980829',
            'onboard_date': '20210910',
            'pol': 'OAKLAND, CA (US)',
            'TYPE': 'CntrMove',
        }
