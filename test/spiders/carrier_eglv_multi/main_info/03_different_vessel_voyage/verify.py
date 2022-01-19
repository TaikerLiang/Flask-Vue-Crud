class Verifier:
    def verify_hidden_info(self, results):
        assert results == {
            "mbl_no": "142901393381",
            "pol_code": "CNSHG",
            "pod_code": "USLGB",
            "onboard_date": "20191004",
            "podctry": "US",
        }

    def verify_basic_info(self, results):
        assert results == {
            "por_name": "SHANGHAI (CN)",
            "pol_name": "SHANGHAI (CN)",
            "pod_name": "LONG BEACH, CA (US)",
            "dest_name": None,
            "place_of_deliv_name": "LOS ANGELES, CA (US)",
            "etd": "OCT-04-2019",
            "cargo_cutoff_date": None,
        }

    def verify_vessel_info(self, results):
        assert results == {
            "eta": None,
            "vessel": None,
            "voyage": None,
        }
