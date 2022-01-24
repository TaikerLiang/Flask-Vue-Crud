class Verifier:
    def verify_hidden_info(self, results):
        assert results == {
            "mbl_no": "003903689108",
            "pol_code": "TWKSG",
            "pod_code": "USBOS",
            "onboard_date": "20200105",
            "podctry": "US",
        }

    def verify_basic_info(self, results):
        assert results == {
            "por_name": "KEELUNG (TW)",
            "pol_name": "KAOHSIUNG (TW)",
            "pod_name": "BOSTON, MA (US)",
            "dest_name": None,
            "place_of_deliv_name": "BOSTON, MA (US)",
            "etd": "JAN-05-2020",
            "cargo_cutoff_date": "DEC-31-2019 12:00",
        }

    def verify_vessel_info(self, results):
        assert results == {
            "eta": "FEB-12-2020",
            "vessel": "EVER LIVEN",
            "voyage": "0935-040E",
        }
