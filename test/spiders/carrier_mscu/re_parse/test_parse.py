import pytest

from crawler.spiders.carrier_mscu import Extractor


@pytest.mark.parametrize('mbl_no_text,expect', [
    ('Bill of lading: MEDUN4194175 (1 container)', 'MEDUN4194175'),
    ('Bill of lading: MEDUH3870035 ', 'MEDUH3870035'),
])
def test_parse_mbl_no(mbl_no_text, expect):
    extractor = Extractor()
    result = extractor._parse_mbl_no(mbl_no_text=mbl_no_text)
    assert result == expect


@pytest.mark.parametrize('container_no_text,expect', [
    ('Container: GLDU7636572', 'GLDU7636572'),
])
def test_re_parse(container_no_text, expect):
    extractor = Extractor()
    result = extractor._parse_container_no(container_no_text=container_no_text)
    assert result == expect


@pytest.mark.parametrize('latest_update_message,expect', [
    (
        'Tracking results provided by MSC on 05.11.2019 at 10:50 W. Europe Standard Time',
        '05.11.2019 at 10:50 W. Europe Standard Time',
    ),
])
def test_re_parse(latest_update_message, expect):
    extractor = Extractor()
    result = extractor._parse_latest_update(latest_update_message=latest_update_message)
    assert result == expect
