class Verifier:
    def verify_hidden_info(self, results):
        assert results == {
            "mbl_no": "003902245109",
            "pol_code": "TWKSG",
            "pod_code": "USBOS",
            "onboard_date": "20190818",
            "podctry": "US",
        }

    def verify_basic_info(self, results):
        assert results == {
            "por_name": "KAOHSIUNG (TW)",
            "pol_name": "KAOHSIUNG (TW)",
            "pod_name": "BOSTON, MA (US)",
            "dest_name": None,
            "place_of_deliv_name": "BOSTON, MA (US)",
            "etd": "AUG-18-2019",
            "cargo_cutoff_date": None,
        }

    def verify_vessel_info(self, results):
        assert results == {
            "eta": "SEP-25-2019",
            "vessel": "EVER LIVEN",
            "voyage": "0915-038E",
        }
