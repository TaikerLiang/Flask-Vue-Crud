from crawler.core_carrier.items import MblItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            us_filing_status='Filing OK',
            us_filing_date='JUL-10-2019',
            task_id='1',
        )
