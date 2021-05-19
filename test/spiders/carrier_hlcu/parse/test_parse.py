import pytest

from crawler.spiders.carrier_hlcu import TracingRoutingRule


@pytest.mark.parametrize(
    'cookie_text,expect',
    [
        (
            (
                'TS01a3c52a=01541c804a3dfa684516e96cae7a588b5eea6236b8843ebfc7882ca3e47063c4b3fd'
                'dc7cc2e58145e71bee2973391cc28597744f23343d7d2544d27a2ce90ca4b356ffb78f5; Path=/'
            ),
            (
                'TS01a3c52a',
                (
                    '01541c804a3dfa684516e96cae7a588b5eea6236b8843ebfc7882ca3e47063c4b3fddc'
                    '7cc2e58145e71bee2973391cc28597744f23343d7d2544d27a2ce90ca4b356ffb78f5'
                ),
            ),
        ),
        (
            'TSff5ac71e_27=081ecde62cab2000428f3620d78d07ee66ace44f9dc6c6feb6bc1bab646fbc7179082123944d1'
            '473084af55ddf1120009050da999bcc34164749e3339b930c12ec88cf3b1cfb6cd3b77b94f5d061834e;Path=/',
            (
                'TSff5ac71e_27',
                (
                    '081ecde62cab2000428f3620d78d07ee66ace44f9dc6c6feb6bc1bab646fbc7179082123944d1473'
                    '084af55ddf1120009050da999bcc34164749e3339b930c12ec88cf3b1cfb6cd3b77b94f5d061834e'
                ),
            ),
        ),
    ],
)
def test_parse_cookie(cookie_text, expect):
    rule = TracingRoutingRule()
    result = rule._parse_cookie(cookie_text)
    assert result == expect
