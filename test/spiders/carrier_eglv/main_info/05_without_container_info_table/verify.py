from crawler.core_carrier.items import MblItem, LocationItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='003903689108',
            vessel='EVER LIVEN',
            voyage='0935-040E',
            por=LocationItem(name='KEELUNG (TW)'),
            pol=LocationItem(name='KAOHSIUNG (TW)'),
            pod=LocationItem(name='BOSTON, MA (US)'),
            place_of_deliv=LocationItem(name='BOSTON, MA (US)'),
            etd='JAN-05-2020',
            final_dest=LocationItem(name=None),
            eta='FEB-12-2020',
            cargo_cutoff_date='DEC-31-2019 12:00',
        )
