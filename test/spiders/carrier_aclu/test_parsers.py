import re

import pytest

from crawler.spiders.carrier_aclu import (
    TimeStatusParser, StatusInfo, LocationTimeStatusParser, VesselLocationTimeStatusParser,
    LoadedFullWithETAStatusParser, LoadedFullStatusParser,
)


@pytest.mark.parametrize('patt,status_text,expect', [
    (
        re.compile(
            r'^(?P<description>Stripped at) On (?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Stripped at On 09/27/19 00:00',
        [
            StatusInfo(
                description='Stripped at',
                local_date_time='09/27/19 00:00',
            ),
        ]
    ),
])
def test_stripped_at(patt, status_text, expect):
    parser = TimeStatusParser(patt=patt)

    match = parser.match(status_text=status_text)
    result = parser.process(match_dict=match.groupdict())

    assert result == expect


@pytest.mark.parametrize('patt,status_text,expect', [
    (
        re.compile(
            r'^(?P<description>Departed empty for) (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Departed empty for Hamburg (Unikai Shed 48),Germany 20457 On 11/05/18 18:45',
        [
            StatusInfo(
                description='Departed empty for',
                location='Hamburg (Unikai Shed 48),Germany 20457',
                local_date_time='11/05/18 18:45',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Discharged empty at) (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Discharged empty at Antwerpen-Kaai 1333(Aet),Belgium 9130 On 06/27/19 12:24',
        [
            StatusInfo(
                description='Discharged empty at',
                location='Antwerpen-Kaai 1333(Aet),Belgium 9130',
                local_date_time='06/27/19 12:24',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Received empty at) (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Received empty at Port Newark,Nj(C&C Maint-Eb2),U.S.A. 07114 On 10/04/17 13:54',
        [
            StatusInfo(
                description='Received empty at',
                location='Port Newark,Nj(C&C Maint-Eb2),U.S.A. 07114',
                local_date_time='10/04/17 13:54',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Departed for) (?P<location>.+) On (?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Departed for Dublin-Port,Ireland On 09/25/17 08:00',
        [
            StatusInfo(
                description='Departed for',
                location='Dublin-Port,Ireland',
                local_date_time='09/25/17 08:00',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Departed from) (?P<location>.+) On (?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Departed from New York-Maher Terminal B64,New York,U.S.A. 07201 On 05/24/19 13:18',
        [
            StatusInfo(
                description='Departed from',
                location='New York-Maher Terminal B64,New York,U.S.A. 07201',
                local_date_time='05/24/19 13:18',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Received at) (?P<location>.+) On (?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Received at Dublin-Port,Ireland On 01/08/18 08:18',
        [
            StatusInfo(
                description='Received at',
                location='Dublin-Port,Ireland',
                local_date_time='01/08/18 08:18',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Scaled in at) (?P<location>.+) On (?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Scaled in at Hamburg-H.C.C.R.,Germany 21129 On 12/27/16 10:00',
        [
            StatusInfo(
                description='Scaled in at',
                location='Hamburg-H.C.C.R.,Germany 21129',
                local_date_time='12/27/16 10:00',
            ),
        ]
    ),
])
def test_location_time(patt, status_text, expect):
    parser = LocationTimeStatusParser(patt=patt)

    match = parser.match(status_text=status_text)
    result = parser.process(match_dict=match.groupdict())

    assert result == expect


@pytest.mark.parametrize('patt,status_text,expect', [
    (
        re.compile(
            r'^(?P<description>Discharged from vessel (?P<vessel>.+)) at (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Discharged from vessel ATLANTIC STAR/AST3419 at Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114 On '
        '07/21/19 10:08',
        [
            StatusInfo(
                description='Discharged from vessel ATLANTIC STAR/AST3419',
                location='Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114',
                local_date_time='07/21/19 10:08',
                vessel='ATLANTIC STAR/AST3419',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Received for vessel (?P<vessel>.+)) at (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Received for vessel ATLANTIC SAIL /7211 at Hamburg (Unikai Shed 48),Germany 20457 On 01/10/17 15:34',
        [
            StatusInfo(
                description='Received for vessel ATLANTIC SAIL /7211',
                location='Hamburg (Unikai Shed 48),Germany 20457',
                local_date_time='01/10/17 15:34',
                vessel='ATLANTIC SAIL /7211',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Received from vessel (?P<vessel>.+)) at (?P<location>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Received from vessel ST. LOUIS EXPRESS /SLX2819 at Charleston-N. Charleston,South Carolina,U.S.A. 29401 '
        'On 02/20/19 06:57',
        [
            StatusInfo(
                description='Received from vessel ST. LOUIS EXPRESS /SLX2819',
                location='Charleston-N. Charleston,South Carolina,U.S.A. 29401',
                local_date_time='02/20/19 06:57',
                vessel='ST. LOUIS EXPRESS /SLX2819',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Departed for) (?P<location>.+) for vessel (?P<vessel>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Departed for Liverpool Seaforth,United Kingdom L21.1 for vessel ATLANTIC SAIL /8262 On 01/17/18 19:27',
        [
             StatusInfo(
                 description='Departed for',
                 location='Liverpool Seaforth,United Kingdom L21.1',
                 local_date_time='01/17/18 19:27',
                 vessel='ATLANTIC SAIL /8262',
             ),
        ]
    ),
    (
        re.compile(
            r'^(?P<description>Departed from) (?P<location>.+) from vessel (?P<vessel>.+) On '
            r'(?P<local_date_time>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Departed from Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114 from vessel ATLANTIC STAR/AST3419 '
        'On 07/23/19 11:36',
        [
            StatusInfo(
                description='Departed from',
                location='Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114',
                local_date_time='07/23/19 11:36',
                vessel='ATLANTIC STAR/AST3419',
            ),
        ]
    ),
])
def test_vessel_location_time(patt, status_text, expect):
    parser = VesselLocationTimeStatusParser(patt=patt)

    match = parser.match(status_text=status_text)
    result = parser.process(match_dict=match.groupdict())

    assert result == expect


@pytest.mark.parametrize('patt,status_text,expect', [
    (
        re.compile(
            r'^(?P<load_event>Loaded full on vessel (?P<vessel>.+)) for (?P<location>.+) On '
            r'(?P<local_date_time1>\w{2}/\w{2}/\w{2} \w{2}:\w{2}) which (?P<sail_event>sailed on) '
            r'(?P<local_date_time2>\w{2}/\w{2}/\w{2} \w{2}:\w{2})\. '
            r'(?P<eta_event>The ETA at the port of Discharge) will be '
            r'(?P<local_date_time3>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Loaded full on vessel ATLANTIC SAIL /8262 for Halifax-Ceres Terminal,Nova Scotia,Canada '
        'On 01/22/18 05:47 which sailed on 01/22/18 12:36. The ETA at the port of Discharge will be 01/31/18 08:00',
        [
            StatusInfo(
                description='The ETA at the port of Discharge',
                location='Halifax-Ceres Terminal,Nova Scotia,Canada',
                local_date_time='01/31/18 08:00',
                vessel='ATLANTIC SAIL /8262',
            ),
            StatusInfo(
                description='sailed on',
                local_date_time='01/22/18 12:36',
                vessel='ATLANTIC SAIL /8262',
            ),
            StatusInfo(
                description='Loaded full on vessel ATLANTIC SAIL /8262',
                local_date_time='01/22/18 05:47',
                vessel='ATLANTIC SAIL /8262',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<load_event>Loaded full on vessel (?P<vessel>.+)) for (?P<location>.+) On '
            r'(?P<local_date_time1>\w{2}/\w{2}/\w{2} \w{2}:\w{2}) (?P<sail_event>Sail Date) '
            r'(?P<local_date_time2>\w{2}/\w{2}/\w{2} \w{2}:\w{2})\. '
            r'(?P<eta_event>The ETA at the port of Discharge) -'
            r'(?P<local_date_time3>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Loaded full on vessel GRANDE ATLANTICO/GAT0519 for Leixoes - Tcl,Portugal 4000 '
        'On 10/13/19 06:44 Sail Date 10/13/19 23:16. The ETA at the port of Discharge -10/21/19 02:20',
        [
            StatusInfo(
                description='The ETA at the port of Discharge',
                location='Leixoes - Tcl,Portugal 4000',
                local_date_time='10/21/19 02:20',
                vessel='GRANDE ATLANTICO/GAT0519',
            ),
            StatusInfo(
                description='Sail Date',
                local_date_time='10/13/19 23:16',
                vessel='GRANDE ATLANTICO/GAT0519',
            ),
            StatusInfo(
                description='Loaded full on vessel GRANDE ATLANTICO/GAT0519',
                local_date_time='10/13/19 06:44',
                vessel='GRANDE ATLANTICO/GAT0519',
            ),
        ]
    ),
])
def test_loaded_full_with_eta(patt, status_text, expect):
    parser = LoadedFullWithETAStatusParser(patt=patt)

    match = parser.match(status_text=status_text)
    result = parser.process(match_dict=match.groupdict())

    assert result == expect


@pytest.mark.parametrize('patt,status_text,expect', [
    (
        re.compile(
            r'^(?P<load_event>Loaded full on vessel (?P<vessel>.+)) for (?P<location>.+) On '
            r'(?P<local_date_time1>\w{2}/\w{2}/\w{2} \w{2}:\w{2}) which (?P<sail_event>sailed on) '
            r'(?P<local_date_time2>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Loaded full on vessel ITEA/8356 for Liverpool Seaforth,United Kingdom L21.1 On 12/20/17 02:25 '
        'which sailed on 12/20/17 16:42',
        [
            StatusInfo(
                description='sailed on',
                local_date_time='12/20/17 16:42',
                vessel='ITEA/8356',
            ),
            StatusInfo(
                description='Loaded full on vessel ITEA/8356',
                local_date_time='12/20/17 02:25',
                vessel='ITEA/8356',
            ),
        ]
    ),
    (
        re.compile(
            r'^(?P<load_event>Loaded full on vessel (?P<vessel>.+)) for (?P<location>.+) On '
            r'(?P<local_date_time1>\w{2}/\w{2}/\w{2} \w{2}:\w{2}) (?P<sail_event>Sail Date) '
            r'(?P<local_date_time2>\w{2}/\w{2}/\w{2} \w{2}:\w{2})'
        ),
        'Loaded full on vessel ATLANTIC STAR/AST3419 for Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114 '
        'On 07/10/19 07:08 Sail Date 07/11/19 04:42',
        [
            StatusInfo(
                description='Sail Date',
                local_date_time='07/11/19 04:42',
                vessel='ATLANTIC STAR/AST3419',
            ),
            StatusInfo(
                description='Loaded full on vessel ATLANTIC STAR/AST3419',
                local_date_time='07/10/19 07:08',
                vessel='ATLANTIC STAR/AST3419',
            ),
        ]
    ),
])
def test_loaded_full(patt, status_text, expect):
    parser = LoadedFullStatusParser(patt=patt)

    match = parser.match(status_text=status_text)
    result = parser.process(match_dict=match.groupdict())

    assert result == expect
