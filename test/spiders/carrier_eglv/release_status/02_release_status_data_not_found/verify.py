from crawler.core_carrier.items_new import MblItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            carrier_status=None,
            carrier_release_date=None,
            us_customs_status=None,
            us_customs_date=None,
            customs_release_status=None,
            customs_release_date=None,
        )
