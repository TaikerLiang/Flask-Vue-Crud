from crawler.core_carrier.items_new import MblItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            us_filing_status="Filing OK",
            us_filing_date="AUG-16-2019",
        )
