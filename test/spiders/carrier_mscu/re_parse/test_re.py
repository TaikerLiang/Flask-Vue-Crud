import pytest

from crawler.spiders.carrier_mscu import Extractor

latest_update_message = 'Tracking results provided by MSC on 05.11.2019 at 10:50 W. Europe Standard Time'
extractor = Extractor()


@pytest.mark.parametrize('parse_fun,input_text,expect_answer', [
    (extractor._parse_mbl_no, 'Bill of lading: MEDUN4194175 (1 container)', 'MEDUN4194175'),
    (extractor._parse_container_no, 'Container: GLDU7636572', 'GLDU7636572'),
    (extractor._parse_latest_update, latest_update_message, '05.11.2019 at 10:50 W. Europe Standard Time'),
])
def test_re_parse(parse_fun, input_text, expect_answer):
    assert parse_fun(input_text) == expect_answer
