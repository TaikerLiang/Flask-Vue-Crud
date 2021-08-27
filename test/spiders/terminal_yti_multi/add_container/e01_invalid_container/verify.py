from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.voyagecontrol_share_spider import ListTracedContainerRoutingRule
from crawler.spiders.terminal_yti_multi import TerminalYtiSpider

def verify(results: List):
    assert isinstance(results[0], InvalidContainerNoItem)