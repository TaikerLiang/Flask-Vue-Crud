class Verifier:
    def verify_hidden_info(self, results):
        assert results == {
            "mbl_no": "003901793951",
            "pol_code": "TWKSG",
            "pod_code": "USBAL",
            "onboard_date": "20190717",
            "podctry": "US",
        }

    def verify_basic_info(self, results):
        assert results == {
            "por_name": "TAICHUNG (TW)",
            "pol_name": "KAOHSIUNG (TW)",
            "pod_name": "BALTIMORE, MD (US)",
            "dest_name": None,
            "place_of_deliv_name": "BALTIMORE, MD (US)",
            "etd": "JUL-17-2019",
            "cargo_cutoff_date": None,
        }

    def verify_vessel_info(self, results):
        assert results == {
            "eta": None,
            "vessel": None,
            "voyage": None,
        }
