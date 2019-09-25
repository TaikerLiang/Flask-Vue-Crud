from crawler.core_carrier.items import MblItem


class Verifier:

    def verify(self, results):
        assert results[0] == MblItem(
            carrier_status='Released',
            carrier_release_date='JUL-08-2019',
            us_customs_status='VVS07649389',
            us_customs_date='JUL-05-2019',
            customs_release_status='RELEASED',
            customs_release_date='JUL-17-2019',
        )
