def verify(results):
    assert results[0] == {"date": "", "status": ""}
    assert results[1] == {
        "ata": "18 Mar 2020, 23:25 JPT",
        "atd": "01 Mar 2020, 05:02 PST",
        "deliv_ata": "24 Mar 2020, 08:19 JPT",
        "deliv_eta": None,
        "eta": None,
        "etd": None,
        "final_dest": "Osaka, Japan",
        "place_of_deliv": "Nanko C-7",
        "pod": "Kobe, Hyogo-ken, Japan",
        "pol": "Los Angeles, Los Angeles, California, United States",
        "por": "Los Angeles, Los Angeles, California, United States",
        "vessel": "NYK ALTAIR",
        "voyage": "049W",
    }
