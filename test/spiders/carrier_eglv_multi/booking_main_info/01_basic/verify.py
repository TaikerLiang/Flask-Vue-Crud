class Verifier:
    def verify_booking_no_and_vessel_voyage(self, results):
        assert results == {
            "booking_no": "456110381786",
            "vessel": "EVER FAME",
            "voyage": "1203-003W",
        }

    def verify_basic(self, results):
        assert results == {
            "por_name": "OAKLAND, CA (US)",
            "pol_name": "OAKLAND, CA (US)",
            "pod_name": "TAIPEI (TW)",
            "place_of_deliv_name": "KEELUNG (TW)",
            "cargo_cutoff_date": "SEP-01-2021",
            "etd": "SEP-10-2021",
            "eta": "SEP-22-2021",
            "onboard_date": "SEP-10-2021",
        }

    def verify_filing_info(self, results):
        assert results == {
            "filing_status": None,
            "filing_date": None,
        }

    def verify_container_infos(self, results):
        assert results == [
            {
                "container_no": "EITU1980829",
                "full_pickup_date": None,
                "empty_pickup_date": "AUG-27-2021 10:46",
            }
        ]
