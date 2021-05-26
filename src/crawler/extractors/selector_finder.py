import abc
from typing import List

import scrapy


class BaseMatchRule:
    @abc.abstractmethod
    def check(self, selector: scrapy.Selector) -> bool:
        pass


def find_selector_from(selectors: List[scrapy.Selector], rule: BaseMatchRule):
    for selector in selectors:
        if rule.check(selector=selector):
            return selector

    return None


# -------------------------------------------------------------------------------
# Custom MatchRule
# -------------------------------------------------------------------------------


class CssQueryExistMatchRule(BaseMatchRule):
    def __init__(self, css_query: str):
        self._css_query = css_query

    def check(self, selector: scrapy.Selector) -> bool:
        existence = selector.css(self._css_query)
        return bool(existence)


class CssQueryTextStartswithMatchRule(BaseMatchRule):
    def __init__(self, css_query: str, startswith: str):
        self._css_query = css_query
        self._startswith = startswith

    def check(self, selector: scrapy.Selector) -> bool:
        text = selector.css(self._css_query).get()

        if not isinstance(text, str):
            return False

        return text.strip().startswith(self._startswith)
