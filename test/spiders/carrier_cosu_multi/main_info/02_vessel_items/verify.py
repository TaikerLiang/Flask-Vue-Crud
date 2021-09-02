from crawler.core_carrier.items import VesselItem, LocationItem


def verify(items):
    assert len(items) == 2

    assert items[0] == VesselItem(
        **{
            'task_id': '2',
            'vessel_key': 'PHUOC LONG 8',
            'vessel': 'PHUOC LONG 8',
            'voyage': '044E',
            'pol': LocationItem(**{'name': 'Phnom Penh'}),
            'pod': LocationItem(**{'name': 'Ba Ria-Vung Tau(CM-TV)'}),
            'etd': '2021-03-02 13:00',
            'atd': None,
            'eta': '2021-03-04 17:00',
            'ata': None,
        }
    )

    assert items[1] == VesselItem(
        **{
            'task_id': '2',
            'vessel_key': 'APL SENTOSA',
            'vessel': 'APL SENTOSA',
            'voyage': '0TUGFE1MA',
            'pol': LocationItem(**{'name': 'Ba Ria-Vung Tau(CM-TV)'}),
            'pod': LocationItem(**{'name': 'Los Angeles'}),
            'etd': '2021-03-12 18:00',
            'atd': None,
            'eta': '2021-04-10 18:00',
            'ata': None,
        }
    )