from crawler.core_vessel.items import VesselPortItem


def verify(results):

    assert len(results) == 13

    assert results[0] == VesselPortItem(
        etd='15 Mar 2020, 17:00 Sun',
        atd='15 Mar 2020, 17:38 Sun',
        eta='12 Mar 2020, 08:00 Thu',
        ata='12 Mar 2020, 05:06 Thu',
        name='Los Angeles',
        un_lo_code='USLAX',
    )

    assert results[1] == VesselPortItem(
        etd='20 Mar 2020, 17:00 Fri',
        atd='20 Mar 2020, 05:09 Fri',
        eta='18 Mar 2020, 18:00 Wed',
        ata='18 Mar 2020, 18:19 Wed',
        name='Oakland',
        un_lo_code='USOAK',
    )

    assert results[2] == VesselPortItem(
        etd='08 Apr 2020, 03:00 Wed',
        atd=None,
        eta='07 Apr 2020, 08:00 Tue',
        ata=None,
        name='Hong Kong',
        un_lo_code='HKHKG',
    )

    assert results[12] == VesselPortItem(
        etd='20 May 2020, 03:00 Wed',
        atd=None,
        eta='19 May 2020, 07:00 Tue',
        ata=None,
        name='Charleston',
        un_lo_code='USCHS',
    )
