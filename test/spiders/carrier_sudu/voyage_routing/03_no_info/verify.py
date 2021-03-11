def verify(results):
    # normally 0: VesselItem, 1: MblSearchRequestOption
    # no vessel item return
    assert len(results) == 1

