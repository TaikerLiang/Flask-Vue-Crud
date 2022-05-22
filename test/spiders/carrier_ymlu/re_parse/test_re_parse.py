import pytest

from crawler.core_carrier.exceptions import CarrierResponseFormatError
from crawler.spiders.carrier_ymlu import MainInfoRoutingRule

ROUTING_RULE = MainInfoRoutingRule()


@pytest.mark.parametrize(
    "time_status, expect_actual_time, expect_estimated_time",
    [
        ("2019/10/08 17:15 (Actual)", "2019/10/08 17:15", None),
        ("2019/10/09 20:00 (Estimated)", None, "2019/10/09 20:00"),
        ("(Estimated)", None, None),
    ],
)
def test_parse_time_status(time_status, expect_actual_time, expect_estimated_time):
    actual_time, estimated_time = ROUTING_RULE._parse_time_status(time_status)

    assert actual_time == expect_actual_time
    assert estimated_time == expect_estimated_time


@pytest.mark.parametrize(
    "carrier_status, expect_status, expect_time",
    [
        ("Steamship Release 2019/09/19 15:00", "Steamship Release", "2019/09/19 15:00"),
    ],
)
def test_parse_carrier_status(carrier_status, expect_status, expect_time):
    status, time = ROUTING_RULE._parse_carrier_status(carrier_status)

    assert status == expect_status
    assert time == expect_time


@pytest.mark.parametrize(
    "firms_code_text, expect_firms_code",
    [
        ("(Firms code:Y258)", "Y258"),
        ("(Firms code:AAA2)", "AAA2"),
        ("(Firms code:)", None),
        (" ", None),
    ],
)
def test_parse_firms_code(firms_code_text, expect_firms_code):
    firms_code = ROUTING_RULE._parse_firms_code(firms_code_text)

    assert firms_code == expect_firms_code


@pytest.mark.parametrize(
    "time_status, func, expect_error",
    [
        ("Steamship Release 2019/09/19 15:0", ROUTING_RULE._parse_carrier_status, CarrierResponseFormatError),
    ],
)
def test_error(time_status, func, expect_error):
    with pytest.raises(expect_error):
        func(time_status)
