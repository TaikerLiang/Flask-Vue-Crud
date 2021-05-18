import abc

from typing import List

from crawler.core_vessel.request_helpers import RequestOption


class BaseRoutingRule:
    name = ''

    @staticmethod
    def build_request_option(*args, **kwargs) -> RequestOption:
        raise NotImplementedError()

    def get_save_name(self, response) -> str:
        """There are multiple types of return result(html, json), so need to overwrite this
        method for every routing rule
        """
        return self.name

    @abc.abstractmethod
    def handle(self, response):
        pass


class RuleManager:
    META_VESSEL_CORE_RULE_NAME = 'VESSEL_CORE_RULE_NAME'

    def __init__(self, rules: List[BaseRoutingRule]):
        self._rule_map = {r.name: r for r in rules}

    def get_rule_by_response(self, response) -> BaseRoutingRule:
        rule_name = response.meta[self.META_VESSEL_CORE_RULE_NAME]
        rule = self._rule_map[rule_name]
        return rule
