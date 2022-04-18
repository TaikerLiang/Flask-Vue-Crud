from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.stg_share_spider import ContainerRoutingRule


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ContainerRoutingRule.name
    assert results[0].meta == {
        "search_no": "OOLU2681547221",
    }
    assert results[0].body == "locationCode=&searchBy=lineBl&searchValue=OOLU2681547221"

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == ContainerRoutingRule.name
    assert results[1].meta == {
        "search_no": "OOLU2561512130",
    }
    assert results[1].body == "locationCode=&searchBy=lineBl&searchValue=OOLU2561512130"
