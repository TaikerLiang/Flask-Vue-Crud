from crawler.core_carrier.items import MblItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            us_filing_status=None,
            us_filing_date=None,
            task_id='1',
        )
