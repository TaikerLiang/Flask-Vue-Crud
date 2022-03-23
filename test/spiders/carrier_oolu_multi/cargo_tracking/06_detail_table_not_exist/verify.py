def verify(results):
    assert results[0] == {"date": "25 Nov 2020, 19:30 GMT", "status": "Cleared"}
    assert results[1] == {
        "ata": "",
        "atd": "",
        "deliv_ata": "",
        "deliv_eta": "",
        "eta": "",
        "etd": "",
        "final_dest": "",
        "place_of_deliv": "",
        "pod": "",
        "pol": "",
        "por": "",
        "vessel": "",
        "voyage": "",
    }
