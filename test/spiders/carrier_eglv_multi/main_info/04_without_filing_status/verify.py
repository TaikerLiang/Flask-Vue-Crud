class Verifier:
    def verify_hidden_info(self, results):
        assert results == {
            "mbl_no": "100980089898",
            "pol_code": "INMUN",
            "pod_code": "USLAX",
            "onboard_date": "20191127",
            "podctry": "US",
        }

    def verify_basic_info(self, results):
        assert results == {
            "por_name": "LUDHIANA (IN)",
            "pol_name": "MUNDRA (IN)",
            "pod_name": "LOS ANGELES, CA (US)",
            "dest_name": None,
            "place_of_deliv_name": "LONG BEACH, CA (US)",
            "etd": "NOV-27-2019",
            "cargo_cutoff_date": "NOV-22-2019 17:30",
        }

    def verify_vessel_info(self, results):
        assert results == {
            "eta": "JAN-01-2020",
            "vessel": "EVER LYRIC",
            "voyage": "1010-032E",
        }
