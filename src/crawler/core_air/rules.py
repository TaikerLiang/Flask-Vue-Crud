import abc

from typing import List

from crawler.core_air.request_helpers import RequestOption


class BaseRoutingRule:
    name = ""

    @staticmethod
    def build_request_option(*args, **kwargs) -> RequestOption:
        raise NotImplementedError()

    def get_save_name(self, response) -> str:
        return self.name

    @abc.abstractmethod
    def handle(self, response):
        pass


class RuleManager:
    META_AIR_CORE_RULE_NAME = "AIR_CORE_RULE_NAME"

    def __init__(self, rules: List[BaseRoutingRule]):
        self._rule_map = {r.name: r for r in rules}

    def get_rule_by_response(self, response) -> BaseRoutingRule:
        rule_name = response.meta[self.META_AIR_CORE_RULE_NAME]
        rule = self._rule_map[rule_name]
        return rule
